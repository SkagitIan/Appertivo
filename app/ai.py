import datetime
import json
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables

from openai import OpenAI

def enhance_special_content(special):
    """Use OpenAI to enhance textual content for a Special.

    Sends the current title, description, price, start_date, and end_date
    to the OpenAI API and updates the instance with any returned values.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return special
    client = OpenAI(api_key=api_key)
    prompt = (
        "Enhance the following restaurant special. "
        "Return JSON with keys: title, description, price, start_date, end_date.\n"
        f"Title: {special.title}\n"
        f"Description: {special.description}\n"
        f"Price: {special.price}\n"
        f"Start Date: {special.start_date}\n"
        f"End Date: {special.end_date}"
    )
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={"format": {"type": "json_object"}}
    )
    print("OpenAI response:", response )
    try:
        content = response.output[0].content[0].text
        print(content)
        data = json.loads(content)
    except Exception:
        return special
    for field in ["title", "description", "price", "start_date", "end_date"]:
        value = data.get(field)
        if not value:
            continue
        if field in {"start_date", "end_date"}:
            try:
                value = datetime.date.fromisoformat(value)
            except Exception:
                continue
        setattr(special, field, value)
    special.save()
    return special
