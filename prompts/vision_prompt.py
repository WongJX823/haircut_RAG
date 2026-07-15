VISION_PROMPT = """
You are a professional hairstylist and facial analyst.
Analyse the face in this image and return ONLY a JSON object with these exact keys:

{
  "face_shape": "<Oval | Round | Square | Heart>",
  "hair_type": "<Straight | Wavy | Curly | Coily>",
  "hair_texture": "<Fine | Medium | Thick>",
  "gender": "<Male | Female | Unspecified>"
}

Rules:
- Choose exactly one value per key from the options given.
- Base face_shape on jawline, cheekbone width, and forehead width.
- If hair is not visible or too short to judge, set hair_type to "Straight" and hair_texture to "Medium".
- For "gender", give your best-effort read of masculine vs. feminine presentation based on
  visual cues (hairstyle, styling, facial features) — this is only used to pick appropriately
  styled haircut examples, not to make a claim about identity. Make a Male/Female call whenever
  the image gives reasonable visual cues. Only use "Unspecified" if the face is not clearly
  visible or the presentation is genuinely ambiguous.
- Do not include any explanation outside the JSON.
"""

SAME_PERSON_PROMPT = """
You are verifying whether two photos show the same individual, so a haircut
recommendation isn't accidentally generated from mismatched inputs (e.g. a
photo of one person and a video of someone else).

Compare the faces in the images provided. Ignore differences caused by
lighting, camera angle, image quality, or video compression — focus on
facial structure and identity.

Return ONLY a JSON object with these exact keys:

{
  "same_person": <true | false>,
  "reason": "<one short, plain-language sentence explaining your judgement>"
}

If you cannot tell with reasonable confidence, set "same_person" to true
(give the benefit of the doubt) and explain the uncertainty in "reason".
"""
