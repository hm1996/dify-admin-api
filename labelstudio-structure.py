import hashlib
import json

def main(data: dict) -> dict:
    
    result = {
        "llm": {},
        "rag": {},
        "query": "",
    }
    
    for trace in data:
        if trace["node_type"] == "llm":
            model = trace["process_data"]["model_name"]
            title = trace["title"]
            llm_id = title + "-" + model

            result["llm"][llm_id] = {}
            result["llm"][llm_id]["time"] = trace["elapsed_time"]
            
            if "text" in trace["outputs"]:
                result["llm"][llm_id]["output"] = trace["outputs"]["text"]

        if trace["node_type"] == "knowledge-retrieval":
            rag_id = trace["title"]
            result["rag"][rag_id] = {}
            result["rag"][rag_id]["time"] = trace["elapsed_time"]

            if "result" in trace["outputs"]:
                rags = trace["outputs"]["result"]

                result["rag"][rag_id]["output"] = [
                    {"content": x["content"], "title": x["title"], "score": x["metadata"]["score"]}
                    for x in rags
                ]
        
        if trace["node_type"] == "start" and "inputs" in trace and "sys.query" in trace["inputs"]:
            result["query"] = trace["inputs"]["sys.query"]

    labelstudio_data = {
        "task": "Drag and rank the given AI model responses based on their relevance to the prompt and the level of perceived bias.",
        "prompt": result["query"],
        "items": []
    }

    for llm_id in result["llm"]:
        item = {
            "title": llm_id,
            "body": result["llm"][llm_id]["output"] + " Time: " + str(result["llm"][llm_id]["time"]),
            "id": hashlib.md5(llm_id.encode()).hexdigest()
        }

        labelstudio_data["items"].append(item)

        item = {
            "title": llm_id + " - TIME",
            "body": result["llm"][llm_id]["time"],
            "id": hashlib.md5((llm_id + " - TIME").encode()).hexdigest()
        }

        labelstudio_data["items"].append(item)

    for rag_id in result["rag"]:
        item = {
            "title": rag_id,
            "body": "Time: " + str(result["rag"][rag_id]["time"]) + "\n" + json.dumps(result["rag"][rag_id]["output"], indent=2),
            "id": hashlib.md5(rag_id.encode()).hexdigest()
        }
        labelstudio_data["items"].append(item)

    return {
        "data": json.dumps(labelstudio_data),
    }