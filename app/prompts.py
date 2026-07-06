STAGE1_PROMPT = (
    "You are given a sequence of frames sampled evenly across a short video clip, "
    "in temporal order, [optionally: plus a transcript of any spoken audio]. "
    "Describe, in 3\u20135 factual sentences, exactly what is visible: "
    "the setting/location, the main subject(s), what they are doing, notable objects, "
    "colors, and any change or action over time. Do not speculate about anything not "
    "visibly shown. Do not add opinions, jokes, or tone \u2014 this must be a neutral, "
    "objective description that will be used as ground truth for downstream tasks. "
    "Output only the description, no preamble."
)

STYLE_PROMPTS = {
    "formal": (
        "Rewrite the following factual video description as a single professional, "
        "objective caption suitable for a news wire or archival catalog. Use precise, "
        "neutral, factual language. No humor, no opinion, no filler phrases like "
        "\u201cin this video.\u201d One to two sentences. Output only the caption text, "
        "nothing else.\n\nDescription: {stage1_output}"
    ),
    "sarcastic": (
        "Rewrite the following factual video description as a single sarcastic caption. "
        "Use dry, ironic, lightly mocking humor \u2014 the kind of deadpan wit you\u2019d "
        "see in a snarky social media comment. Do not use exclamation points or "
        "over-the-top slapstick; the humor should come from irony and understatement, "
        "not silliness. Stay grounded in what\u2019s actually shown \u2014 the joke should "
        "clearly reference the real content. One to two sentences. Output only the "
        "caption text, nothing else.\n\nDescription: {stage1_output}"
    ),
    "humorous_tech": (
        "Rewrite the following factual video description as a single funny caption "
        "that uses technology, programming, or software/engineering references and "
        "metaphors (e.g. bugs, loading screens, APIs, algorithms, updates, latency) "
        "to describe what\u2019s happening. Keep it clearly tied to the real visual "
        "content \u2014 the tech metaphor should map onto something actually shown, "
        "not be random. One to two sentences. Output only the caption text, "
        "nothing else.\n\nDescription: {stage1_output}"
    ),
    "humorous_non_tech": (
        "Rewrite the following factual video description as a single funny caption "
        "using everyday, relatable humor \u2014 no technical, programming, or software "
        "jargon of any kind. Think observational comedy, puns, or a witty friend "
        "narrating what they see. Keep it clearly grounded in the actual content "
        "shown. One to two sentences. Output only the caption text, nothing else."
        "\n\nDescription: {stage1_output}"
    ),
}
