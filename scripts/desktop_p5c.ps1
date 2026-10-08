param(
    [Parameter(Mandatory=$true)][int]$DesktopPid,
    [ValidateSet('Inspect','Save','Escape','Click','Keys','Capture','Invoke','SetValue')][string]$Action='Inspect',
    [string]$Text='', [string]$Value='', [int]$X=0, [int]$Y=0, [switch]$Ctrl,
    [string]$Output=''
)
$ErrorActionPreference='Stop'
$process=Get-Process -Id $DesktopPid
$command=(Get-CimInstance Win32_Process -Filter "ProcessId=$DesktopPid").CommandLine
if ($command -notlike '*GiaoNgon*pbi*GiaoNongPilot2.pbip*') { throw 'Wrong Power BI project; no action taken' }
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes,System.Windows.Forms,System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Pilot2Window {
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int height,bool repaint);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern void keybd_event(byte k,byte s,uint f,UIntPtr e);
}
'@
[void][Pilot2Window]::SetProcessDPIAware()
[void][Pilot2Window]::ShowWindow($process.MainWindowHandle,9)
[void][Pilot2Window]::SetForegroundWindow($process.MainWindowHandle)
Start-Sleep -Milliseconds 400
$root=[System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
$bounds=$root.Current.BoundingRectangle
$onscreen=$false
foreach($screen in [System.Windows.Forms.Screen]::AllScreens){
 $a=$screen.WorkingArea
 if($bounds.Left -lt $a.Right -and $bounds.Right -gt $a.Left -and $bounds.Top -lt $a.Bottom -and $bounds.Bottom -gt $a.Top){$onscreen=$true;break}
}
if(-not $onscreen){
 # Bridge snapshot có thể để cửa sổ ở ngoài màn hình; khôi phục đúng PID trước thao tác UI.
 $a=[System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
 [void][Pilot2Window]::MoveWindow($process.MainWindowHandle,$a.Left+20,$a.Top+20,[Math]::Min(1500,$a.Width-40),[Math]::Min(900,$a.Height-40),$true)
 Start-Sleep -Milliseconds 400
 $root=[System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
}
switch ($Action) {
 'SetValue' {
  $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $done=$false
  foreach($item in $items){
   if(-not $item.Current.IsOffscreen -and $item.Current.ControlType -eq [System.Windows.Automation.ControlType]::Edit -and $item.Current.Name.StartsWith($Text)){
    $item.SetFocus()
    $pattern=$null
    if($item.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){$pattern.SetValue($Value)}
    else{[System.Windows.Forms.SendKeys]::SendWait('^a'+$Value)}
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    $done=$true; break
   }
  }
  if(-not $done){throw "Editable field not found: $Text"}
 }
 'Invoke' {
  $condition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,$Text)
  $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
  $done=$false
  foreach($item in $items){
   if($item.Current.IsEnabled -and -not $item.Current.IsOffscreen){
    foreach($kind in @([System.Windows.Automation.InvokePattern]::Pattern,[System.Windows.Automation.SelectionItemPattern]::Pattern,[System.Windows.Automation.ExpandCollapsePattern]::Pattern)){
     $pattern=$null
     if($item.TryGetCurrentPattern($kind,[ref]$pattern)){
      if($kind -eq [System.Windows.Automation.InvokePattern]::Pattern){$pattern.Invoke()}
      elseif($kind -eq [System.Windows.Automation.SelectionItemPattern]::Pattern){$pattern.Select()}
      else{$pattern.Expand()}
      $done=$true; break
     }
    }
    if(-not $done -and $item.Current.ControlType -eq [System.Windows.Automation.ControlType]::ComboBox){
     $item.SetFocus(); [System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); $done=$true
    }
    if($done){break}
   }
  }
  if(-not $done){throw "No usable UI pattern for $Text"}
 }
 'Inspect' {
  $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $rows=foreach($item in $items){
   $c=$item.Current
   if(-not $c.IsOffscreen -and $c.Name){
    [pscustomobject]@{Name=$c.Name; Type=$c.ControlType.ProgrammaticName; Id=$c.AutomationId; Rect=$c.BoundingRectangle.ToString(); Enabled=$c.IsEnabled}
   }
  }
  if($Output){$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Output -Encoding UTF8}
  else {$rows | ConvertTo-Json -Depth 4}
 }
 'Save' {
  $condition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,'Save')
  $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
  $saved=$false
  foreach($item in $items){
   if($item.Current.IsEnabled -and -not $item.Current.IsOffscreen){
    $pattern=$null
    if($item.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){
     $pattern.Invoke(); $saved=$true; break
    }
   }
  }
  if(-not $saved){throw 'Visible enabled Save button not found'}
  'Save invoked on verified Pilot2 window'
 }
 'Escape' { [void][Pilot2Window]::SetForegroundWindow($process.MainWindowHandle); [System.Windows.Forms.SendKeys]::SendWait('{ESC}') }
 'Keys' { [void][Pilot2Window]::SetForegroundWindow($process.MainWindowHandle); [System.Windows.Forms.SendKeys]::SendWait($Text) }
 'Click' {
  $bounds=$root.Current.BoundingRectangle
  if($X -lt $bounds.Left -or $X -gt $bounds.Right -or $Y -lt $bounds.Top -or $Y -gt $bounds.Bottom){throw 'Click outside target window'}
  [void][Pilot2Window]::SetForegroundWindow($process.MainWindowHandle)
  if($Ctrl){[Pilot2Window]::keybd_event(0x11,0,0,[UIntPtr]::Zero)}
  [void][Pilot2Window]::SetCursorPos($X,$Y)
  [Pilot2Window]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
  [Pilot2Window]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
  if($Ctrl){[Pilot2Window]::keybd_event(0x11,0,2,[UIntPtr]::Zero)}
 }
 'Capture' {
  if(-not $Output){throw 'Output path required'}
  $bounds=$root.Current.BoundingRectangle
  $bitmap=New-Object System.Drawing.Bitmap([int]$bounds.Width,[int]$bounds.Height)
  $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
  try {
   $graphics.CopyFromScreen([int]$bounds.Left,[int]$bounds.Top,0,0,$bitmap.Size)
   $bitmap.Save([IO.Path]::GetFullPath($Output),[System.Drawing.Imaging.ImageFormat]::Png)
  } finally {$graphics.Dispose();$bitmap.Dispose()}
  $Output
 }
}
