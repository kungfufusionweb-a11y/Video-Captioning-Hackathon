Analyze this entire codebase thoroughly and produce a markdown file named 
`tech&features.md` in the project root. Do not skip files — walk through 
every directory, config file, and dependency manifest before writing anything.

Structure the file with these exact sections:

## 1. Tech Stack
- List every language, framework, and major library used (check package.json, 
  requirements.txt, or equivalent dependency files)
- Identify the frontend framework/stack
- Identify the backend framework/stack
- Identify database(s) used and how they're connected
- Identify any cloud services, storage, or third-party APIs integrated 
  (e.g. storage buckets, hosting, auth providers)
- Note the audio/video processing libraries specifically — list every library 
  or API involved in audio input, preprocessing, transcription, or output

## 2. Audio Processing Pipeline (detailed)
- Trace the exact flow: from audio upload/input to final transcript output
- Explicitly state whether any noise reduction, noise cancellation, or audio 
  cleaning step exists in the code (name the specific library/function if so). 
  If there is no such step, say so explicitly — do not assume or guess.
- Identify which transcription model/API is being called and how
- Note any language-detection or multilingual handling logic

## 3. Features (Core)
- List every user-facing feature you can find evidence of in the code 
  (not just what a README claims — verify against actual implemented logic/routes/UI)
- For each feature, briefly note which files/modules implement it

## 4. AI/ML Features Specifically
- List every place the code calls an AI model or ML capability
- For each: what model/API, what it's used for, and any pre/post-processing 
  around the call

## 5. Known Bugs & Issues
- Flag any incomplete functions, TODO/FIXME comments, unhandled error cases, 
  or logic that looks broken or inconsistent
- Flag any hardcoded values, missing error handling, or edge cases not covered
- Note any language/accent/audio conditions where transcription logic looks 
  likely to fail or degrade (based on code inspection, not just guessing)
- Be specific: file name, function name, and what's wrong

## 6. Architecture Overview
- Brief description of how the pieces connect (e.g. frontend → API → 
  processing → storage → database)
- Note any real-time or streaming components and how they're implemented

## 7. Gaps & Extension Opportunities
- Based on the above, list concrete features that are NOT yet implemented 
  but would be natural extensions
- List concrete technical improvements that would fix the bugs found in 
  Section 5

## 8. File Structure Map
- Generate a full directory tree (excluding node_modules, .git, build/dist 
  folders, and other generated artifacts)
- For each major folder, write one line describing its purpose based on 
  what's actually inside it
- Identify any structural inconsistencies: files in the wrong place, 
  inconsistent naming conventions (e.g. mixed camelCase/kebab-case), 
  duplicate/orphaned files, or components that logically belong together 
  but are scattered across different folders

## 9. Component Inventory
- List every React component file, its file path, and one sentence on what 
  it renders/does
- Note component size (rough line count) — flag any component over ~300 
  lines as a candidate for splitting
- Note prop-drilling patterns: are props passed through multiple component 
  layers unnecessarily? Identify specific examples with file/line references
- Note any components that mix concerns (e.g. a component doing both data 
  fetching AND complex rendering AND state management) as refactor candidates
  
Be precise and evidence-based throughout — cite actual file paths and function 
names for every claim. Do not describe features or technologies that aren't 
actually present in the code, even if they seem implied by naming conventions 
or comments. If something is unclear or ambiguous from the code alone, say so 
rather than assuming.