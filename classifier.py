import json
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "phi3"


SUPPORTED_TYPES = [
    "rectangle",
    "circle",
    "triangle",
    "helix",
    "sphere",
    "cone",
    "pyramid",
    "wedge",
    "mesh",
    "l_bracket",
    "washer",
    "shaft",
    "flange",
    "o_ring",
    "pulley",
    "sprocket",
    "spur_gear",
    "hex_bolt",
    "machine_screw",
    "hex_nut",
    "compression_spring",
    "extension_spring",
    "bevel_gear",
    "helical_gear",
]


def normalize_response(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("-", "_")
    text = text.replace(" ", "_")
    text = text.replace(".", "")
    text = text.replace(",", "")
    text = text.replace("`", "")
    text = text.replace('"', "")
    text = text.replace("'", "")
    return text


def classify_operation(prompt: str) -> str:
    p = prompt.lower().strip()

    if any(word in p for word in ["extrude", "make it 3d", "make 3d", "pull"]):
        return "extrude"

    if any(word in p for word in ["hole", "cut", "drill", "punch"]):
        return "cut_hole"

    return "create_shape"


def keyword_classify_shape(prompt: str) -> str:
    p = prompt.lower().strip()

    if "compression spring" in p:
        return "compression_spring"
    if "extension spring" in p:
        return "extension_spring"
    if "bevel gear" in p:
        return "bevel_gear"
    if "helical gear" in p:
        return "helical_gear"

    if "hex bolt" in p or "bolt" in p:
        return "hex_bolt"
    if "machine screw" in p or "screw" in p:
        return "machine_screw"
    if "hex nut" in p or "nut" in p:
        return "hex_nut"

    if "l bracket" in p or "l-bracket" in p or "angle bracket" in p:
        return "l_bracket"
    if "washer" in p:
        return "washer"
    if "shaft" in p or "rod" in p:
        return "shaft"
    if "flange" in p:
        return "flange"
    if "o-ring" in p or "oring" in p or "rubber ring" in p:
        return "o_ring"
    if "pulley" in p:
        return "pulley"
    if "sprocket" in p or "chain wheel" in p or "chainwheel" in p:
        return "sprocket"
    if "spur gear" in p:
        return "spur_gear"
    if "gear" in p or "cog" in p:
        return "spur_gear"

    if "helix" in p or "spiral" in p:
        return "helix"
    if "sphere" in p or "ball" in p:
        return "sphere"
    if "cone" in p:
        return "cone"
    if "pyramid" in p:
        return "pyramid"
    if "wedge" in p:
        return "wedge"
    if "mesh" in p:
        return "mesh"
    if "circle" in p or "round" in p:
        return "circle"
    if "cylinder" in p:
        return "circle"
    if "rectangle" in p or "square" in p or "box" in p or "plate" in p:
        return "rectangle"
    if "triangle" in p or "triangular" in p:
        return "triangle"

    return "unknown"


def ask_ollama_shape(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 25,
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a CAD command classifier.\n"
                    "Return ONLY one object type from this exact list:\n"
                    + ", ".join(SUPPORTED_TYPES)
                    + "\n\n"
                    "Rules:\n"
                    "- Return only the object type.\n"
                    "- Do not explain.\n"
                    "- Do not write code.\n"
                    "- Do not use punctuation.\n"
                    "- If the request is unclear, return unknown.\n"
                    "- sprocket means chain wheel.\n"
                    "- round 2D shape means circle.\n"
                    "- box or square plate means rectangle.\n"
                    "- threaded fastener usually means hex_bolt.\n"
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        text = normalize_response(result["message"]["content"])

        if text in SUPPORTED_TYPES:
            return text

        for supported_type in SUPPORTED_TYPES:
            if supported_type in text:
                return supported_type

        return "unknown"

    except Exception:
        return "unknown"


def classify_shape(prompt: str) -> str:
    """
    AI-first classifier:
    1. Ask Ollama first.
    2. If Ollama fails or returns unknown, use keyword fallback.
    """

    ai_result = ask_ollama_shape(prompt)

    if ai_result != "unknown":
        return ai_result

    return keyword_classify_shape(prompt)


def classify(prompt: str) -> dict:
    operation = classify_operation(prompt)

    if operation != "create_shape":
        return {
            "operation": operation,
            "shape": None,
        }

    shape = classify_shape(prompt)

    return {
        "operation": operation,
        "shape": shape,
    }


if __name__ == "__main__":
    while True:
        user_prompt = input("CAD prompt: ").strip()

        if user_prompt.lower() in ["exit", "quit"]:
            break

        result = classify(user_prompt)
        print(result)