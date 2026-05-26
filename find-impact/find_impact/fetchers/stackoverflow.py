import requests
from datetime import datetime, timezone
from typing import List, Dict, Any
from find_impact.config import Config
from find_impact.models import ContentItem
from find_impact.fetchers.base import BaseFetcher


class StackOverflowFetcher(BaseFetcher):
    @property
    def name(self) -> str:
        return "Stack Overflow"

    def fetch(self, config: Config) -> List[ContentItem]:
        user_id = config.stackoverflow_user_id
        if not user_id:
            # Not configured, skip
            return []

        print(f"Fetching Stack Overflow answers for user: {user_id}...")
        base_url = "https://api.stackexchange.com/2.3"
        answers_url = f"{base_url}/users/{user_id}/answers"

        params = {
            "site": "stackoverflow",
            "order": "desc",
            "sort": "activity",
            "pagesize": 100,  # Grab up to 100 answers
        }

        try:
            res = requests.get(answers_url, params=params)
            if res.status_code != 200:
                print(f"Warning: Stack Overflow API returned status {res.status_code}: {res.text}")
                return []

            answers_data = res.json()
            answers = answers_data.get("items", [])
            if not answers:
                print("No Stack Overflow answers found for this user.")
                return []

            # Extract unique question IDs to batch fetch titles
            question_ids = list({str(ans["question_id"]) for ans in answers})

            # Fetch question details in batches of 50 to avoid URL length issues
            questions_map: Dict[int, Dict[str, Any]] = {}
            for i in range(0, len(question_ids), 50):
                batch_ids = question_ids[i : i + 50]
                ids_str = ";".join(batch_ids)
                questions_url = f"{base_url}/questions/{ids_str}"
                q_params = {
                    "site": "stackoverflow",
                    "pagesize": 50,
                }
                q_res = requests.get(questions_url, params=q_params)
                if q_res.status_code == 200:
                    q_data = q_res.json()
                    for q in q_data.get("items", []):
                        questions_map[q["question_id"]] = q
                else:
                    print(
                        f"Warning: Failed to fetch question titles for batch: {q_res.status_code}"
                    )

            # Construct ContentItems
            items: List[ContentItem] = []
            for ans in answers:
                q_id = ans["question_id"]
                ans_id = ans["answer_id"]
                score = ans.get("score", 0)
                is_accepted = ans.get("is_accepted", False)
                creation_date_unix = ans.get("creation_date")

                # Convert unix timestamp to ISO format string
                publish_date = datetime.fromtimestamp(
                    creation_date_unix, tz=timezone.utc
                ).isoformat()

                # Resolve question title
                question = questions_map.get(q_id, {})
                question_title = question.get("title", f"Question #{q_id}")
                # Clean up HTML entities in question title (like &quot;, &#39;)
                question_title = (
                    question_title.replace("&quot;", '"')
                    .replace("&#39;", "'")
                    .replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                )

                url = f"https://stackoverflow.com/questions/{q_id}/#{ans_id}"

                items.append(
                    ContentItem(
                        id=f"stackoverflow-answer-{ans_id}",
                        title=f"[Stack Overflow] Answer to: {question_title}",
                        url=url,
                        platform="stackoverflow",
                        publish_date=publish_date,
                        summary=f"Score: {score} | Accepted: {is_accepted}",
                        metrics={"score": score, "is_accepted": is_accepted},
                        extra_metadata={
                            "question_id": q_id,
                            "answer_id": ans_id,
                            "view_count": question.get("view_count", 0),
                            "tags": question.get("tags", []),
                        },
                    )
                )

            return items

        except Exception as e:
            print(f"Error fetching Stack Overflow answers: {e}")
            return []
