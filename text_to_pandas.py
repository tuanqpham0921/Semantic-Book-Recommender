from llama_cpp import Llama

llm = Llama(model_path="/home/user/models/qwen2.5-3b-instruct-q4_k_m.gguf", 
            n_threads=4, 
            n_ctx=2048,
            verbose=False)


resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "Respond with JSON only."},
        {"role": "user", "content": "Find me a book that’s uplifting, over 300 pages, nonfiction."}
    ],
    temperature=0,
    max_tokens=80,
    grammar=JSON_GRAMMAR, 
)
print(resp["choices"][0]["message"]["content"])
