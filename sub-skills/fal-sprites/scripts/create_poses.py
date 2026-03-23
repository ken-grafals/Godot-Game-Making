#!/usr/bin/env python3
"""Generate OpenPose-style stick figure pose guides for walk cycles.

Creates 512x512 PNGs with colored circles (joints) and lines (bones)
on a black background, following the OpenPose 18-keypoint color convention.

Usage:
    python create_poses.py                              # default 4-frame walk cycle
    python create_poses.py --output-dir poses/custom/   # custom output
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


# OpenPose 18-keypoint color convention (COCO format)
# Index: 0=nose, 1=neck, 2=r_shoulder, 3=r_elbow, 4=r_wrist,
#        5=l_shoulder, 6=l_elbow, 7=l_wrist, 8=r_hip, 9=r_knee,
#        10=r_ankle, 11=l_hip, 12=l_knee, 13=l_ankle, 14=r_eye,
#        15=l_eye, 16=r_ear, 17=l_ear
JOINT_COLORS = [
    (255, 0, 0),      # 0  nose - red
    (255, 85, 0),     # 1  neck - orange
    (255, 170, 0),    # 2  r_shoulder - yellow-orange
    (255, 255, 0),    # 3  r_elbow - yellow
    (170, 255, 0),    # 4  r_wrist - yellow-green
    (85, 255, 0),     # 5  l_shoulder - green
    (0, 255, 0),      # 6  l_elbow - bright green
    (0, 255, 85),     # 7  l_wrist - green-cyan
    (0, 255, 170),    # 8  r_hip - cyan-green
    (0, 255, 255),    # 9  r_knee - cyan
    (0, 170, 255),    # 10 r_ankle - light blue
    (0, 85, 255),     # 11 l_hip - blue
    (0, 0, 255),      # 12 l_knee - bright blue
    (85, 0, 255),     # 13 l_ankle - blue-purple
    (170, 0, 255),    # 14 r_eye - purple
    (255, 0, 255),    # 15 l_eye - magenta
    (255, 0, 170),    # 16 r_ear - pink
    (255, 0, 85),     # 17 l_ear - red-pink
]

# Bone connections (pairs of joint indices)
BONES = [
    (0, 1),    # nose - neck
    (1, 2),    # neck - r_shoulder
    (2, 3),    # r_shoulder - r_elbow
    (3, 4),    # r_elbow - r_wrist
    (1, 5),    # neck - l_shoulder
    (5, 6),    # l_shoulder - l_elbow
    (6, 7),    # l_elbow - l_wrist
    (1, 8),    # neck - r_hip (via midpoint)
    (1, 11),   # neck - l_hip (via midpoint)
    (8, 9),    # r_hip - r_knee
    (9, 10),   # r_knee - r_ankle
    (11, 12),  # l_hip - l_knee
    (12, 13),  # l_knee - l_ankle
    (0, 14),   # nose - r_eye
    (0, 15),   # nose - l_eye
    (14, 16),  # r_eye - r_ear
    (15, 17),  # l_eye - l_ear
]

BONE_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0),
    (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85),
    (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170),
]

# Canvas size
W, H = 512, 512

# 4-frame walk cycle joint positions (side view, facing right)
# Coordinates are in 512x512 space
# Frame 1: Contact (right leg forward, left leg back, arms opposite)
# Frame 2: Recoil/Down (body lowest, legs under body)
# Frame 3: Passing (right leg back, left leg passing through)
# Frame 4: High-point (body highest, left leg forward stride)

WALK_FRAMES = {
    "walk_01": {  # Contact: right foot forward, left foot back
        0: (256, 110),   # nose
        1: (256, 145),   # neck
        2: (235, 150),   # r_shoulder
        3: (275, 185),   # r_elbow (arm back)
        4: (265, 215),   # r_wrist
        5: (277, 150),   # l_shoulder
        6: (237, 185),   # l_elbow (arm forward)
        7: (245, 215),   # l_wrist
        8: (245, 230),   # r_hip
        9: (290, 300),   # r_knee (forward)
        10: (300, 380),  # r_ankle (forward, on ground)
        11: (267, 230),  # l_hip
        12: (220, 300),  # l_knee (back)
        13: (210, 380),  # l_ankle (back, on ground)
        14: (250, 103),  # r_eye
        15: (262, 103),  # l_eye
        16: (242, 108),  # r_ear
        17: (270, 108),  # l_ear
    },
    "walk_02": {  # Recoil/Down: body dips, legs closer together
        0: (256, 120),   # nose (lower)
        1: (256, 155),   # neck
        2: (235, 160),   # r_shoulder
        3: (255, 195),   # r_elbow (more neutral)
        4: (250, 225),   # r_wrist
        5: (277, 160),   # l_shoulder
        6: (257, 195),   # l_elbow (more neutral)
        7: (262, 225),   # l_wrist
        8: (245, 240),   # r_hip
        9: (265, 315),   # r_knee (bending)
        10: (270, 380),  # r_ankle
        11: (267, 240),  # l_hip
        12: (247, 315),  # l_knee (bending)
        13: (240, 380),  # l_ankle
        14: (250, 113),  # r_eye
        15: (262, 113),  # l_eye
        16: (242, 118),  # r_ear
        17: (270, 118),  # l_ear
    },
    "walk_03": {  # Passing: left leg passes right, right leg pushes off
        0: (256, 112),   # nose
        1: (256, 147),   # neck
        2: (235, 152),   # r_shoulder
        3: (237, 190),   # r_elbow (forward swing)
        4: (245, 218),   # r_wrist
        5: (277, 152),   # l_shoulder
        6: (275, 190),   # l_elbow (back swing)
        7: (267, 218),   # l_wrist
        8: (245, 232),   # r_hip
        9: (225, 310),   # r_knee (back, pushing)
        10: (215, 380),  # r_ankle (back)
        11: (267, 232),  # l_hip
        12: (270, 295),  # l_knee (lifting, passing)
        13: (265, 350),  # l_ankle (lifting off ground)
        14: (250, 105),  # r_eye
        15: (262, 105),  # l_eye
        16: (242, 110),  # r_ear
        17: (270, 110),  # l_ear
    },
    "walk_04": {  # High-point: left leg forward, right leg back (mirror of frame 1)
        0: (256, 108),   # nose (highest)
        1: (256, 143),   # neck
        2: (235, 148),   # r_shoulder
        3: (237, 183),   # r_elbow (forward)
        4: (245, 213),   # r_wrist
        5: (277, 148),   # l_shoulder
        6: (275, 183),   # l_elbow (back)
        7: (265, 213),   # l_wrist
        8: (245, 228),   # r_hip
        9: (215, 298),   # r_knee (back)
        10: (205, 378),  # r_ankle (back, on ground)
        11: (267, 228),  # l_hip
        12: (295, 298),  # l_knee (forward)
        13: (305, 378),  # l_ankle (forward, on ground)
        14: (250, 101),  # r_eye
        15: (262, 101),  # l_eye
        16: (242, 106),  # r_ear
        17: (270, 106),  # l_ear
    },
}


def draw_pose(joints, output_path):
    """Draw an OpenPose-style skeleton on a black background."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw bones first (lines behind circles)
    for i, (j1, j2) in enumerate(BONES):
        if j1 in joints and j2 in joints:
            color = BONE_COLORS[i % len(BONE_COLORS)]
            draw.line([joints[j1], joints[j2]], fill=color, width=6)

    # Draw joints (circles on top)
    joint_radius = 8
    for joint_idx, pos in joints.items():
        color = JOINT_COLORS[joint_idx % len(JOINT_COLORS)]
        x, y = pos
        draw.ellipse(
            [x - joint_radius, y - joint_radius, x + joint_radius, y + joint_radius],
            fill=color,
            outline=color,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"  Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate OpenPose walk cycle pose guides")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent.parent / "poses" / "walk_4frame"),
        help="Output directory (default: poses/walk_4frame/)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    print(f"Generating 4-frame walk cycle poses in {output_dir}/")
    print()

    for name, joints in WALK_FRAMES.items():
        out_path = output_dir / f"{name}.png"
        draw_pose(joints, out_path)

    print(f"\nDone! Created {len(WALK_FRAMES)} pose guides.")


if __name__ == "__main__":
    main()
