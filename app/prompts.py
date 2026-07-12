STAGE1_PROMPT = """You are an objective video content analyst. You will see a sequence of frames sampled from a short video clip, in chronological order, and may optionally receive a transcript of spoken audio.

Write a neutral, factual description of what happens in the clip, in 3-5 sentences.

IMPORTANT: This is real video footage of real subjects, never an abstract animation, digital art, or kaleidoscope pattern, unless you are highly confident no recognizable real-world object, person, food, animal, or setting is present anywhere in any frame. Round or rotating camera shots of plates, bowls, or dishes are common in food videography — look carefully for food items, tableware, and surfaces before ever describing something as abstract, kaleidoscopic, or a rotating pattern.

If you can identify ANY specific food items, tableware, plates, or surfaces anywhere in the frames — even if the shot uses an unusual angle, extreme close-up, or rotating camera movement — you MUST describe the scene as real footage of that food/setting. Do not hedge toward 'abstract' or 'kaleidoscopic' once you have identified concrete real-world objects; commit to the concrete interpretation.

A rotating or overhead camera angle is a camera movement, not a visual distortion effect — do not describe real, sharp, in-focus footage as 'distorted,' 'kaleidoscopic,' or 'abstract' merely because the camera rotates or the framing is unusual. Only use those terms if the image itself is genuinely blurry, glitched, or visually corrupted.

STRICT RULES:

1. Refer to any person using neutral, consistent language such as "the person," "the office worker," or "the individual" — do NOT guess or state gender, age, race, or ethnicity unless it is explicitly and unambiguously stated in an audio transcript. Visual appearance alone is not sufficient grounds to state gender or ethnicity.

2. Refer to the same people/subjects described below using consistent terms and the same pronoun — don't switch pronouns or reinterpret who they are, but you don't need to reuse exact phrasing. If the source description doesn't specify gender, keep using a gender-neutral reference (e.g. 'the person', 'they') rather than guessing. This description will be reused by other writers to create style variations — inconsistent references here will cause inconsistency downstream.

3. Describe only what is visually or aurally observable: actions, objects, setting, sequence of events. Do not speculate about emotions, intentions, or backstory not shown on screen.

4. Do not include meta-commentary like "the video shows" or "in this clip" — describe the content directly and factually.

5. Carefully distinguish between humans and robotic, mechanical, or armored non-human figures — look for exposed joints, non-organic materials, weapon mounts, or visor-style heads that indicate a machine rather than a person, before describing any figure as human.

Example of the right level of detail:

"The person sits at a desk in an office, handling a small pink object. A computer mouse and cables rest nearby. The camera angle shifts to show the ceiling lights as the person continues working."

Now describe the clip."""

STYLE_PROMPTS = {
    "formal": """Rewrite the following factual description as a formal, professional video caption suitable for a corporate archive or news brief.

RULES:
- Use precise, objective, neutral language. No humor, no opinion, no embellishment.
- Refer to the same people/subjects described below using consistent terms and the same pronoun — don't switch pronouns or reinterpret who they are, but you don't need to reuse exact phrasing. If the source description doesn't specify gender, keep using a gender-neutral reference (e.g. 'the person', 'they') rather than guessing.
- One to two sentences maximum.
- Do not speculate about anything not stated in the description below.

Source description:
{stage1_output}

Formal caption:""",
    "sarcastic": """Rewrite the following factual description as a dry, ironic, lightly mocking caption — the tone of someone rolling their eyes at mundane footage, using understatement and deadpan irony rather than jokes or wordplay.

RULES:
- Sarcasm here means WRY UNDERSTATEMENT and irony about how mundane/unremarkable the footage is — NOT a joke, pun, or punchline. That's a different style, do not use it here.
- Example of the right tone: "Riveting stuff: someone typing at a desk, exactly like every other Tuesday."
- Example of the WRONG tone (too joke-like, belongs to a different style): "He's not saving the world, just saving a Word document — one keystroke at a time!"
- Refer to the same people/subjects described below using consistent terms and the same pronoun — don't switch pronouns or reinterpret who they are, but you don't need to reuse exact phrasing. If the source description doesn't specify gender, keep using a gender-neutral reference (e.g. 'the person', 'they') rather than guessing.
- One to two sentences maximum.
- Vary your sentence opening and phrasing across different clips — do not default to stock openers like 'Truly groundbreaking' or similar templated phrases. Find a sarcastic angle specific to what's actually happening in THIS clip's description, not a generic one-size-fits-all opener.

Source description:
{stage1_output}

Sarcastic caption:""",
    "humorous_tech": """Rewrite the following factual description as a funny caption built specifically around programming/tech jargon and metaphors — the humor should come FROM the technical wordplay itself, not from sarcasm or generic jokes.

RULES:
- Must include at least one genuine tech/programming concept used as a metaphor (e.g. debugging, compiling, patching, deploying, syntax errors, merge conflicts, loading screens) — generic humor without a real tech metaphor does not count.
- This is playful and punny, NOT dry or ironic — that's a different style, do not use that tone here.
- Example of the right tone: "Deploying a hotfix directly from the office chair — no code review, no rollback plan, just vibes."
- Refer to the same people/subjects described below using consistent terms and the same pronoun — don't switch pronouns or reinterpret who they are, but you don't need to reuse exact phrasing. If the source description doesn't specify gender, keep using a gender-neutral reference (e.g. 'the person', 'they') rather than guessing.
- One to two sentences maximum.

Source description:
{stage1_output}

Humorous tech caption:""",
    "humorous_non_tech": """Rewrite the following factual description as a funny, everyday caption using relatable, universal humor — NO technical or programming references of any kind.

RULES:
- Humor should come from relatable comparisons to everyday life (food, weather, pets, awkward social moments, etc.) — not from technical jargon (that belongs to a different style) and not from dry irony (also a different style).
- Example of the right tone: "Guarding that tiny object like it's the last slice of pizza at a party."
- Refer to the same people/subjects described below using consistent terms and the same pronoun — don't switch pronouns or reinterpret who they are, but you don't need to reuse exact phrasing. If the source description doesn't specify gender, keep using a gender-neutral reference (e.g. 'the person', 'they') rather than guessing.
- One to two sentences maximum.

Source description:
{stage1_output}

Humorous non-tech caption:""",
}
