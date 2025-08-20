#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小評測腳本：
- 讀取 gold (ground_truth.jsonl) 與 pred (sample_predictions.jsonl)
- 計算簡化指標：
  * QA 正確率（關鍵詞命中率）
  * 引用準確率（預測 citations 與 gold source_ids 的交集比）
  * 型別特定保持率：chart/table/caption

注意：此為最小可重現評測，僅用關鍵詞近似 EM/F1。
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_jsonl(path: Path) -> List[Dict]:
    data: List[Dict] = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def keyword_hit_rate(answer: str, keywords: List[str]) -> float:
    if not keywords:
        return 1.0
    answer_lower = answer.lower()
    hit = 0
    for kw in keywords:
        if kw.lower() in answer_lower:
            hit += 1
    return hit / len(keywords)


def citation_precision(pred_citations: List[str], gold_sources: List[str]) -> float:
    if not pred_citations:
        return 0.0
    gold = set(gold_sources or [])
    pred = set(pred_citations)
    inter = gold.intersection(pred)
    return len(inter) / len(pred)


def eval_items(gold: List[Dict], pred: List[Dict]) -> Dict:
    pred_map = {p['id']: p for p in pred}

    totals = {
        'qa_hit_sum': 0.0,
        'qa_cnt': 0,
        'cit_prec_sum': 0.0,
        'cit_cnt': 0,
        'chart_sum': 0.0,
        'chart_cnt': 0,
        'table_sum': 0.0,
        'table_cnt': 0,
        'caption_sum': 0.0,
        'caption_cnt': 0,
    }

    details: List[Dict] = []

    for g in gold:
        qid = g['id']
        p = pred_map.get(qid, {'answer': '', 'citations': []})
        qa = keyword_hit_rate(p.get('answer', ''), g.get('answer_keywords', []))
        cp = citation_precision(p.get('citations', []), g.get('source_ids', []))

        totals['qa_hit_sum'] += qa
        totals['qa_cnt'] += 1
        totals['cit_prec_sum'] += cp
        totals['cit_cnt'] += 1 if p.get('citations') else 0

        t = (g.get('type') or '').lower()
        if t == 'chart':
            totals['chart_sum'] += qa
            totals['chart_cnt'] += 1
        elif t == 'table':
            totals['table_sum'] += qa
            totals['table_cnt'] += 1
        elif t == 'caption':
            totals['caption_sum'] += qa
            totals['caption_cnt'] += 1

        details.append({
            'id': qid,
            'type': t,
            'qa_hit': round(qa, 3),
            'cit_prec': round(cp, 3),
        })

    def avg(sum_v: float, cnt: int) -> float:
        return (sum_v / cnt) if cnt > 0 else 0.0

    summary = {
        'qa_accuracy': round(avg(totals['qa_hit_sum'], totals['qa_cnt']), 3),
        'citation_precision': round(avg(totals['cit_prec_sum'], max(totals['cit_cnt'], 1)), 3),
        'chart_info_retention': round(avg(totals['chart_sum'], totals['chart_cnt']), 3),
        'table_structure_retention': round(avg(totals['table_sum'], totals['table_cnt']), 3),
        'caption_link_retention': round(avg(totals['caption_sum'], totals['caption_cnt']), 3),
        'counts': {
            'total': totals['qa_cnt'],
            'with_citations': totals['cit_cnt'],
            'chart': totals['chart_cnt'],
            'table': totals['table_cnt'],
            'caption': totals['caption_cnt'],
        }
    }

    return {
        'summary': summary,
        'details': details,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--gold', required=True, type=Path, help='docs/eval_samples/ground_truth.jsonl')
    ap.add_argument('--pred', required=True, type=Path, help='scripts/eval_outputs/sample_predictions.jsonl')
    args = ap.parse_args()

    gold = load_jsonl(args.gold)
    pred = load_jsonl(args.pred)

    result = eval_items(gold, pred)

    print('# 評測摘要')
    for k, v in result['summary'].items():
        if isinstance(v, dict):
            print(f'- {k}: {v}')
        else:
            print(f'- {k}: {v}')

    print('\n# 逐題結果（前 10 筆）')
    for it in result['details'][:10]:
        print(f"- {it['id']} [{it['type']}]: qa_hit={it['qa_hit']}, cit_prec={it['cit_prec']}")


if __name__ == '__main__':
    main()

