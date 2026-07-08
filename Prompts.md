Stage 1 — Neutral grounding prompt (vision model):
You are given a sequence of frames sampled evenly across a short video clip, in temporal order, [optionally: plus a transcript of any spoken audio]. Describe, in 3–5 factual sentences, exactly what is visible: the setting/location, the main subject(s), what they are doing, notable objects, colors, and any change or action over time. Do not speculate about anything not visibly shown. Do not add opinions, jokes, or tone — this must be a neutral, objective description that will be used as ground truth for downstream tasks. Output only the description, no preamble.
Stage 2a — Formal:
Rewrite the following factual video description as a single professional, objective caption suitable for a news wire or archival catalog. Use precise, neutral, factual language. No humor, no opinion, no filler phrases like "in this video." One to two sentences. Output only the caption text, nothing else.
Description: {stage1_output}
Stage 2b — Sarcastic:
Rewrite the following factual video description as a single sarcastic caption. Use dry, ironic, lightly mocking humor — the kind of deadpan wit you'd see in a snarky social media comment. Do not use exclamation points or over-the-top slapstick; the humor should come from irony and understatement, not silliness. Stay grounded in what's actually shown — the joke should clearly reference the real content. One to two sentences. Output only the caption text, nothing else.
Description: {stage1_output}
Stage 2c — Humorous-tech:
Rewrite the following factual video description as a single funny caption that uses technology, programming, or software/engineering references and metaphors (e.g. bugs, loading screens, APIs, algorithms, updates, latency) to describe what's happening. Keep it clearly tied to the real visual content — the tech metaphor should map onto something actually shown, not be random. One to two sentences. Output only the caption text, nothing else.
Description: {stage1_output}
Stage 2d — Humorous-non-tech:
Rewrite the following factual video description as a single funny caption using everyday, relatable humor — no technical, programming, or software jargon of any kind. Think observational comedy, puns, or a witty friend narrating what they see. Keep it clearly grounded in the actual content shown. One to two sentences. Output only the caption text, nothing else.
Description: {stage1_output}
Tell OpenCode to store these as named string constants (e.g. STAGE1_PROMPT, STYLE_PROMPTS = {"formal": ..., "sarcastic": ..., "humorous_tech": ..., "humorous_non_tech": ...}) so you can tweak wording later without touching pipeline logic.
2. Sample clip URLs for sample_tasks.json
json[
  {
    "task_id": "v1",
    "video_url": "https://storage.googleapis.com/amd-hackathon-clips/1860079-uhd_2560_1440_25fps.mp4",
    "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
  },
  {
    "task_id": "v2",
    "video_url": "https://storage.googleapis.com/amd-hackathon-clips/13825391-uhd_3840_2160_30fps.mp4",
    "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
  },
  {
    "task_id": "v3",
    "video_url": "https://storage.googleapis.com/amd-hackathon-clips/3044693-uhd_3840_2160_24fps.mp4",
    "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
  }
]