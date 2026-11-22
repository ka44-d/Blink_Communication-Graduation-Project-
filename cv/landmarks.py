"""MediaPipe Face Mesh landmark indices (anatomical: 'left'/'right' = the SUBJECT's eyes).

Eye order is p1..p6 for EAR: p1/p4 horizontal corners, (p2,p6) and (p3,p5) vertical pairs.
Input frames must NOT be mirrored before landmarking, or left/right swap (see config.swap_eyes).
"""
RIGHT_EYE = (33, 160, 158, 133, 153, 144)
LEFT_EYE = (362, 385, 387, 263, 373, 380)
HEAD_POSE_IDS = (1, 152, 33, 263, 61, 291)   # nose, chin, eye outer corners, mouth corners
BLENDSHAPE_LEFT = "eyeBlinkLeft"
BLENDSHAPE_RIGHT = "eyeBlinkRight"
