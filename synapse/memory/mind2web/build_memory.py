import openai
import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import json
import pickle
from tqdm import tqdm

from synapse.utils.state_abstraction import (
    get_state_abstraction
)

from synapse.envs.mind2web.env_utils import (
    load_json,
    get_target_obs_and_act,
    get_top_k_obs,
)


def get_specifiers_from_sample(sample: dict) -> str:
    website = sample["website"]
    domain = sample["domain"]
    subdomain = sample["subdomain"]
    goal = sample["confirmed_task"]
    specifier = (
        f"Website: {website}\nDomain: {domain}\nSubdomain: {subdomain}\nTask: {goal}"
    )

    return specifier


def build_memory(memory_path: str, data_dir: str, top_k: int = 3):
    openai.api_key = os.environ["OPENAI_API_KEY"]

    score_path = "scores_all_data.pkl"
    with open(os.path.join(data_dir, score_path), "rb") as f:
        candidate_results = pickle.load(f)
    candidate_scores = candidate_results["scores"]
    candidate_ranks = candidate_results["ranks"]

    specifiers = []
    exemplars = []
    samples = load_json(data_dir, "train")
    for sample in tqdm(samples):
        specifiers.append(get_specifiers_from_sample(sample))
        prev_obs = []
        prev_actions = []
        prev_ids = []
        prev_tasks = []
        for s, act_repr in zip(sample["actions"], sample["action_reprs"]):
            # add prediction scores and ranks to candidates
            sample_id = f"{sample['annotation_id']}_{s['action_uid']}"
            for candidates in [s["pos_candidates"], s["neg_candidates"]]:
                for candidate in candidates:
                    candidate_id = candidate["backend_node_id"]
                    candidate["score"] = candidate_scores[sample_id][candidate_id]
                    candidate["rank"] = candidate_ranks[sample_id][candidate_id]

            _, target_act = get_target_obs_and_act(s)
            #target_obs, _ = get_top_k_obs(s, top_k)
            target_obs = get_state_abstraction(sample['website'], s['raw_html'])

            if len(prev_obs) > 0:
                prev_obs.append("Observation: `" + target_obs + "`")
            else:
                query = f"Task: {sample['confirmed_task']}\nTrajectory:\n"
                prev_obs.append(query + "Observation: `" + target_obs + "`")
            prev_actions.append("Action: `" + target_act + "` (" + act_repr + ")")
            prev_ids.append(sample_id)
            prev_tasks.append(sample['confirmed_task'])

        message = []
        for o, a, id, task in zip(prev_obs, prev_actions, prev_ids, prev_tasks):
            message.append({"role": "user", "content": o, "id":(id + "_observation"), "task": task})
            message.append({"role": "assistant", "content": a, "id": (id + "_action"), "task": task})
        exemplars.append(message)

    with open(os.path.join(memory_path, "exemplars.json"), "w") as f:
        json.dump(exemplars, f, indent=2)

    print(f"# of exemplars: {len(exemplars)}")

    # embed memory_keys into VectorDB
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    metadatas = [{"name": i, "annotation_id": samples[i]["annotation_id"]} for i in range(len(specifiers))]
    memory = FAISS.from_texts(
        texts=specifiers,
        embedding=embedding,
        metadatas=metadatas,
    )
    memory.save_local(memory_path)


def retrieve_exemplar_name(memory, query: str, top_k) -> tuple[list[str], list[float]]:
    docs_and_similarities = memory.similarity_search_with_score(query, top_k)
    retrieved_exemplar_names = []
    retrieved_exemplar_ids = []
    scores = []
    for doc, score in docs_and_similarities:
        retrieved_exemplar_names.append(doc.metadata["name"])
        retrieved_exemplar_ids.append(doc.metadata["annotation_id"])
        scores.append(score)

    return retrieved_exemplar_names, scores , retrieved_exemplar_ids


def load_memory(memory_path):
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    memory = FAISS.load_local(memory_path, embedding)

    return memory
