"""Live synthetic study smoke checks; no real learner records or saved answers."""
import argparse
import json
from pathlib import Path
import time
from educator import AGE_BANDS, Educator, Ollama
from study import METHODS, Study
from educator import practice_reference

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='piet-educator')
    parser.add_argument('--judge-model', default='qwen3:8b')
    parser.add_argument('--method', choices=['all'] + list(METHODS), default='all')
    parser.add_argument('--age-band', choices=AGE_BANDS, default='6-9')
    args = parser.parse_args()
    educator = Educator(json.loads((Path(__file__).parent / 'lessons.json').read_text()), args.age_band,
                        Ollama(args.model), Ollama(args.judge_model))
    study = Study(educator)
    failed = False
    for method in METHODS if args.method == 'all' else [args.method]:
        started = time.monotonic()
        card = study.create({'lesson_id':'sharing','method':method,'challenge':'familiar'})
        print(json.dumps({'method':method,'age':args.age_band,'status':card['status'],'seconds':round(time.monotonic()-started,1)}), flush=True)
        failed |= card['status'] != 'checked'
        if card['status'] == 'checked':
            print(json.dumps({k:card[k] for k in ('instruction','worked_example','question')},ensure_ascii=False),flush=True)
            guidance = study.act({'activity_id':card['activity_id'],'action':'reveal'})
            print('SYNTHETIC PRACTICE GUIDANCE: ' + guidance['answer'], flush=True)
            if method in ('recall', 'worked'):
                attempt = 'I thinck each person gets four counters.' if method == 'recall' else 'I thinck ' + guidance['answer'] + ' in this practice example.'
                feedback = study.act({'activity_id':card['activity_id'],'action':'respond','attempt':attempt})
                print(json.dumps({'feedback_status':feedback['status'],'feedback':feedback['answer']}),flush=True)
                failed |= feedback['status'] != 'checked'
                if feedback['status'] == 'checked':
                    checked_reference = practice_reference({'question':card['question'], 'reference_answer':guidance['answer']})
                    failed |= feedback.get('quote_kind') != 'practice' or feedback.get('quote', '') not in checked_reference
    raise SystemExit(1 if failed else 0)
