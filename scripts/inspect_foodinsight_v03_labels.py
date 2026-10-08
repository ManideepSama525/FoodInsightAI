import argparse, json
from pathlib import Path
from datasets import load_dataset
from transformers import AutoTokenizer

SYSTEM = (
    "You are FoodInsight-LM, an evidence-aware food intelligence model. "
    "Use only supplied evidence for factual claims. "
    "If evidence is insufficient, say so explicitly. "
    "Preserve numeric values and units. "
    "Do not invent sources, nutrients, portions, or facts."
)

def build_messages(ex):
    return [
        {"role":"system","content":SYSTEM},
        {"role":"user","content":
            f"Question:\n{ex['question']}\n\n"
            f"Evidence:\n{ex.get('context','')}\n\n"
            "Give a concise evidence-grounded answer."}
    ]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-model",required=True)
    ap.add_argument("--train",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--limit",type=int,default=20)
    args=ap.parse_args()

    tok=AutoTokenizer.from_pretrained(args.base_model,trust_remote_code=True)
    ds=load_dataset("json",data_files=args.train,split="train")
    n=min(args.limit,len(ds))
    rows=[]

    im_end=tok.convert_tokens_to_ids("<|im_end|>")
    eos=tok.eos_token_id

    for i in range(n):
        ex=ds[i]
        messages=build_messages(ex)
        prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        full=tok.apply_chat_template(
            messages+[{"role":"assistant","content":str(ex["answer"])}],
            tokenize=False,add_generation_prompt=False
        )

        pids=tok(prompt,add_special_tokens=False)["input_ids"]
        fids=tok(full,add_special_tokens=False)["input_ids"]

        # Reproduce the training label-mask logic used by V0.3.
        labels=fids.copy()
        prompt_len=min(len(pids),len(labels))
        labels[:prompt_len]=[-100]*prompt_len

        supervised=[x for x in labels if x != -100]
        decoded_supervised=tok.decode(supervised,skip_special_tokens=False)
        tail=tok.decode(fids[-40:],skip_special_tokens=False)

        rows.append({
            "index":i,
            "question":ex["question"],
            "answer":str(ex["answer"]),
            "prompt_tokens":len(pids),
            "full_tokens":len(fids),
            "supervised_tokens":len(supervised),
            "last_full_token_ids":fids[-20:],
            "last_supervised_token_ids":supervised[-20:],
            "eos_in_supervised":eos in supervised,
            "im_end_in_supervised":im_end in supervised,
            "decoded_supervised_tail":decoded_supervised[-500:],
            "decoded_full_tail":tail,
            "supervised_equals_answer_text":decoded_supervised.strip().endswith(str(ex["answer"]).strip()),
        })

    report={
        "examples":n,
        "tokenizer":{
            "eos_token":tok.eos_token,"eos_token_id":eos,
            "im_end_id":im_end,"pad_token_id":tok.pad_token_id
        },
        "results":rows
    }
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Saved:",args.output)
    for r in rows[:5]:
        print(
            f"#{r['index']}: prompt={r['prompt_tokens']} full={r['full_tokens']} "
            f"supervised={r['supervised_tokens']} "
            f"EOS={r['eos_in_supervised']} IM_END={r['im_end_in_supervised']} "
            f"answer_tail_match={r['supervised_equals_answer_text']}"
        )

if __name__=="__main__":
    main()
