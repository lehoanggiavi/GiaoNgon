"""Compute and plot the business narrative; CSV/model/report source files stay read-only."""
import collections
import csv
import hashlib
import json
import pathlib
import statistics
from decimal import Decimal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/business_report'
OUT.mkdir(exist_ok=True)
rows = list(csv.DictReader((ROOT/'data/curated/orders.csv').open(encoding='utf-8-sig')))
assert len(rows) == len({r['order_id'] for r in rows}) == 6073

def group_stats(group):
    eligible = [r for r in group if r['is_cancelled'] == '0']
    late = sum(r['is_late'] == '1' for r in eligible)
    cancelled = sum(r['is_cancelled'] == '1' for r in group)
    return dict(orders=len(group), cancelled=cancelled, eligible=len(eligible), late=late,
                late_rate=late/len(eligible) if eligible else None,
                cancel_rate=cancelled/len(group) if group else None)

def groups(field, key=lambda value:value):
    result = collections.defaultdict(list)
    for row in rows:
        result[key(row[field])].append(row)
    return {label:group_stats(group) for label,group in sorted(result.items())}

month = groups('order_date',lambda value:value[:7])
slot = groups('time_slot')
rain = groups('is_rain')
band = groups('distance_band_normalized')
joint = {}
for evening in [False,True]:
    for wet in [False,True]:
        selected = [r for r in rows if (r['time_slot']=='Tối')==evening and (r['is_rain']=='1')==wet]
        joint[('Tối' if evening else 'Khung khác')+' / '+('Mưa' if wet else 'Không mưa')] = group_stats(selected)
reference = json.loads((ROOT/'reports/phase4b/tables.json').read_text(encoding='utf-8'))
for actual,previous in [(month,reference['month']),(slot,reference['slot']),(rain,reference['rain']),(band,reference['band'])]:
    for label,metrics in actual.items():
        for field,oldfield in [('orders','orders'),('eligible','eligible'),('late','late'),('cancelled','cancel')]:
            assert metrics[field] == previous[label][oldfield],(label,field)
assert sum(v['orders'] for v in joint.values()) == 6073
assert sum(v['late'] for v in joint.values()) == 750
cancelled = [r for r in rows if r['is_cancelled']=='1']
compensation = sum(Decimal(r['compensation']) for r in rows)
cancel_compensation = sum(Decimal(r['compensation']) for r in cancelled)
reason_counts = dict(collections.Counter(r['cancel_reason'] for r in cancelled))
assert cancel_compensation == Decimal(7224000)
assert compensation == Decimal(9999000)
ratings = {label:dict(n=len(selected),mean=statistics.mean(float(r['rating']) for r in selected))
           for label,selected in [('Trễ',[r for r in rows if r['is_late']=='1']),('Đúng giờ',[r for r in rows if r['is_late']=='0'])]}
summary = dict(month=month,slot=slot,rain=rain,band=band,night_rain=joint,
    orders_growth_mar_aug=month['2026-08']['orders']/month['2026-03']['orders']-1,
    late_rate_change_pp=(month['2026-08']['late_rate']-month['2026-03']['late_rate'])*100,
    evening_share_late=slot['Tối']['late']/750,evening_share_cancelled=slot['Tối']['cancelled']/348,
    cancellation_reasons=reason_counts,cancelled_compensation=str(cancel_compensation),
    total_compensation=str(compensation),cancelled_share_compensation=float(cancel_compensation/compensation),
    ratings=ratings,financial={field:str(sum(Decimal(r[field]) for r in rows)) for field in ['order_value','revenue','profit']},
    sourceSha256=hashlib.sha256((ROOT/'data/curated/orders.csv').read_bytes()).hexdigest())
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'axes.labelcolor':'#292524','text.color':'#292524','axes.edgecolor':'#D6D3D1'})
CORAL, GRAY, INK = '#D46C54','#A8A29E','#292524'
fig,axes = plt.subplots(1,2,figsize=(10.4,3.3),constrained_layout=True)
labels = [key[5:] for key in month]
axes[0].bar(labels,[value['orders'] for value in month.values()],color=GRAY)
axes[0].set_title('Số đơn ghi nhận tăng về cuối kỳ',loc='left',fontweight='bold')
axes[0].set_ylabel('Đơn'); axes[0].set_xlabel('Tháng / 2026')
for i,value in enumerate(month.values()): axes[0].text(i,value['orders']+15,str(value['orders']),ha='center',fontsize=9)
axes[0].set_ylim(0,1350)
for field,color,label in [('late_rate',CORAL,'Trễ / đơn đủ dữ liệu'),('cancel_rate',INK,'Hủy / tổng đơn')]:
    values=[value[field]*100 for value in month.values()]
    axes[1].plot(labels,values,marker='o',color=color,label=label)
    axes[1].annotate(f'{values[-1]:.2f}%',(5,values[-1]),xytext=(-5,8),textcoords='offset points',ha='right',fontsize=9,color=color)
axes[1].set_title('Hủy và trễ tăng mạnh ở tháng 8',loc='left',fontweight='bold')
axes[1].set_ylabel('Tỷ lệ (%)'); axes[1].set_ylim(0,30); axes[1].legend(frameon=False,loc='upper left',fontsize=8)
fig.savefig(OUT/'monthly_story.png',dpi=180); plt.close(fig)

ranked = sorted(slot.items(),key=lambda pair:pair[1]['late'])
fig,ax = plt.subplots(figsize=(9.5,2.8),constrained_layout=True)
bars=ax.barh([key for key,_ in ranked],[value['late'] for _,value in ranked],color=[CORAL if key=='Tối' else GRAY for key,_ in ranked])
for bar,(_,value) in zip(bars,ranked):
    ax.text(bar.get_width()+5,bar.get_y()+bar.get_height()/2,
        f"{value['late']} đơn · {value['late']/750:.1%} số trễ",va='center',fontsize=9)
ax.set_xlim(0,525); ax.set_xlabel('Số đơn trễ'); ax.set_title('Ca Tối chứa hơn một nửa số đơn trễ',loc='left',fontweight='bold')
fig.savefig(OUT/'evening_priority.png',dpi=180); plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(10.4,3),constrained_layout=True)
reasons=sorted(reason_counts.items(),key=lambda pair:pair[1])
axes[0].barh([key for key,_ in reasons],[value for _,value in reasons],color=GRAY)
for i,(_,value) in enumerate(reasons): axes[0].text(value+3,i,str(value),va='center',fontsize=9)
axes[0].set_xlim(0,230); axes[0].set_title('Lý do hủy được ghi trong nguồn',loc='left',fontweight='bold'); axes[0].set_xlabel('Đơn hủy')
axes[1].bar(list(ratings),[value['mean'] for value in ratings.values()],color=[CORAL,GRAY])
for i,(_,value) in enumerate(ratings.items()):
    axes[1].text(i,value['mean']+.08,f"{value['mean']:.2f}\nn = {value['n']:,}",ha='center',fontsize=9)
axes[1].set_ylim(0,5.4); axes[1].set_title('Điểm thấp đi cùng đơn trễ',loc='left',fontweight='bold'); axes[1].set_ylabel('Điểm trung bình theo nguồn')
fig.savefig(OUT/'business_impact.png',dpi=180); plt.close(fig)
print('Business aggregates reconciled; 3 figures generated; source files untouched.')
