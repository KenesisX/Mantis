"""Faces, 70 moods, 100+ psychic ranks, and the dark Mantis voice.

All text is original, written in the spirit of the character — a sorrowful,
telepathic villain raised into a Tamagotchi-style dark companion. The villain
"deeds" (possession, kidnapping, severing minds) are pure fiction performed on
invented NPCs; they are flavour for a dark pet and are NOT connected to the
real, benign recon tools in spells.py.
"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

random.seed()


def pick(options: List[str]) -> str:
    return random.choice(options) if options else "..."


# --------------------------------------------------------------------------- #
# 100+ psychic ranks — capstone is MANTIS at level 100 (prestige beyond)
# --------------------------------------------------------------------------- #
RANKS: List[Tuple[int, str]] = [
    (1, "Dormant Psyche"), (3, "Flicker"), (5, "Awakened Esper"),
    (8, "Latent Mind"), (11, "Telepath"), (14, "Mindwhisperer"),
    (17, "Mentalist"), (20, "Thoughtstealer"), (24, "Psychic Warrior"),
    (28, "Dreadnought of the Mind"), (32, "Mind Render"), (36, "Soulreader"),
    (40, "Astral Adept"), (44, "Nightmare Weaver"), (48, "Puppeteer"),
    (52, "Mindbreaker"), (56, "Soul Harvester"), (60, "Phantom of FIREFOX"),
    (64, "Dread Esper"), (68, "Void Seer"), (72, "Tyrant of Thought"),
    (76, "Mind Tyrant"), (80, "Harbinger"), (84, "The Sorrowful"),
    (88, "Shade of Shadow Moses"), (90, "Most Powerful Psychic"),
    (94, "Living Nightmare"), (97, "The Unmasked Dread"), (100, "MANTIS"),
]
LEVEL_CAP = 100


def rank_for(level: int) -> str:
    if level >= LEVEL_CAP:
        extra = level - LEVEL_CAP
        if extra <= 0:
            return "MANTIS"
        return "MANTIS " + "✦" * min(5, 1 + extra // 10)
    title = RANKS[0][1]
    for threshold, name in RANKS:
        if level >= threshold:
            title = name
        else:
            break
    return title


# --------------------------------------------------------------------------- #
# Mood registry.  Each mood declares how the e-ink sprite is drawn:
#   eyes : normal narrow wide closed half slit glow star cross cracked spiral tear
#   aura : none waves lightning flame smoke void halo static
#   pose : float arms_raised arms_out slump curl reach crucifix hover point
#   fx   : none zzz tarot skull chains ghost blood crown question
#   web  : which of the 9 SVG/ASCII expressions to fall back to
#   dark : contributes to / reflects the darkness theme
# --------------------------------------------------------------------------- #
MOODS: Dict[str, dict] = {}
CLUSTERS: Dict[str, List[str]] = {}


def _M(name, cluster, eyes, aura, pose, fx, dark, web, *phrases):
    MOODS[name] = {"c": cluster, "eyes": eyes, "aura": aura, "pose": pose,
                   "fx": fx, "dark": dark, "web": web, "p": list(phrases)}
    CLUSTERS.setdefault(cluster, []).append(name)


# ---- idle / watching ------------------------------------------------------ #
_M("watching", "idle", "normal", "none", "float", "none", False, "watching",
   "I can read your mind...", "Behind this mask I see everything.",
   "Every signal is a thought. I hear them all.")
_M("listening", "idle", "normal", "waves", "float", "none", False, "watching",
   "The ether whispers your secrets to me.", "Be still. I am listening.")
_M("brooding", "idle", "narrow", "smoke", "float", "none", True, "smug",
   "So much hatred in the world... and I feel all of it.",
   "The dark suits me better than the light ever did.")
_M("lurking", "idle", "slit", "void", "float", "none", True, "smug",
   "You did not see me arrive. You never do.", "I am the shadow in your signal.")
_M("calculating", "idle", "narrow", "none", "point", "none", False, "distracted",
   "I have already seen how this ends.", "Every outcome, mapped. Every mind, read.")
_M("curious", "idle", "wide", "none", "float", "question", False, "watching",
   "What are you thinking, right now? ...I know.", "A new mind. How interesting.")
_M("observing", "idle", "normal", "none", "float", "none", False, "watching",
   "I watch. I wait. I know.", "Nothing escapes the mask.")

# ---- content / cared-for -------------------------------------------------- #
_M("serene", "content", "closed", "halo", "float", "none", False, "pleased",
   "For a moment... the voices are quiet.", "Peace. I had forgotten the word.")
_M("content", "content", "normal", "halo", "float", "none", False, "pleased",
   "You keep me whole. I will remember that.", "This is... almost happiness.")
_M("amused", "content", "narrow", "none", "float", "none", False, "smug",
   "You amuse me, little keeper.", "Heh. Predictable, but charming.")
_M("playful", "content", "wide", "none", "hover", "none", False, "pleased",
   "Shall I move something, just to watch your face?", "Catch. ...Made you flinch.")
_M("meditative", "content", "closed", "waves", "float", "none", False, "pleased",
   "I gather the chaos into a single still point.", "Breathe in the thoughts. Exhale control.")
_M("affectionate", "content", "normal", "halo", "float", "none", False, "pleased",
   "Kindness. I had almost forgotten it existed.", "You are not afraid of me. Why?")
_M("tranquil", "content", "closed", "none", "float", "none", False, "pleased",
   "Still water. Still mind.", "The storm sleeps, for now.")

# ---- smug / triumphant ---------------------------------------------------- #
_M("smug", "smug", "narrow", "none", "float", "none", False, "smug",
   "There is no one who can stand before me.", "Predictable. Beautifully predictable.")
_M("triumphant", "smug", "wide", "lightning", "arms_raised", "crown", False, "overcharged",
   "Bow. You all bow eventually.", "I told you how this would end.")
_M("mocking", "smug", "narrow", "none", "point", "none", True, "smug",
   "Is that your best thought? Pitiful.", "You cannot hide what you are from me.")
_M("prophetic", "smug", "glow", "waves", "arms_out", "tarot", False, "casting",
   "The cards already told me you would come.", "I see your fate laid bare.")
_M("omniscient", "smug", "glow", "halo", "float", "none", False, "smug",
   "I know everything you have ever feared.", "Your mind is an open book to me.")
_M("superior", "smug", "narrow", "none", "float", "crown", True, "smug",
   "You are pawns. I am the hand.", "Kneel, or be made to kneel.")

# ---- hunger --------------------------------------------------------------- #
_M("starving", "hunger", "wide", "none", "reach", "none", False, "hungry",
   "Feed me a memory... I am starving.", "I cannot read the ether on an empty soul.")
_M("ravenous", "hunger", "wide", "flame", "reach", "skull", True, "hungry",
   "I will DEVOUR a mind if you will not feed me.", "Hunger makes monsters of us all.")
_M("hollow", "hunger", "slit", "smoke", "slump", "none", True, "hungry",
   "There is a void where my strength should be.", "Empty. So empty.")
_M("gnawing", "hunger", "narrow", "none", "curl", "none", False, "hungry",
   "The hunger gnaws at my thoughts.", "Give me something. Anything.")

# ---- low energy ----------------------------------------------------------- #
_M("drowsy", "energy", "half", "none", "float", "zzz", False, "sleeping",
   "Let me rest in the dark behind the mask...", "Even a psychic must dream.")
_M("weary", "energy", "half", "none", "slump", "none", False, "sleeping",
   "My power thins. I must rest.", "So tired of carrying every mind at once.")
_M("fading", "energy", "half", "smoke", "slump", "none", True, "sleeping",
   "I am fading from the waking world...", "The light grows dim. Let it.")
_M("dreaming", "energy", "closed", "waves", "curl", "zzz", False, "sleeping",
   "I walk the astral plane in my sleep.", "In dreams, no one can abandon me.")
_M("astral_drift", "energy", "closed", "void", "float", "ghost", True, "sleeping",
   "My spirit drifts far from this body.", "Do not wake the vessel. I am elsewhere.")
_M("comatose", "energy", "closed", "none", "curl", "none", False, "sleeping",
   "......", "The mask goes dark.")

# ---- low focus ------------------------------------------------------------ #
_M("scattered", "focus", "spiral", "static", "float", "question", False, "distracted",
   "Too many thoughts... I cannot hold them.", "The signal fractures into noise.")
_M("static", "focus", "wide", "static", "float", "none", False, "distracted",
   "Static. Everywhere static.", "I can't hear your mind through the noise.")
_M("dizzy", "focus", "spiral", "none", "float", "question", False, "distracted",
   "The visions spin and will not settle.", "Which thought is yours? Which is mine?")
_M("clouded", "focus", "half", "smoke", "float", "none", True, "distracted",
   "A fog has rolled over my mind.", "I cannot see the futures clearly.")
_M("unfocused", "focus", "wide", "static", "float", "question", False, "distracted",
   "Concentration slips through my fingers.", "Help me find the single thread again.")

# ---- low sanity ----------------------------------------------------------- #
_M("uneasy", "sanity", "wide", "smoke", "float", "none", True, "distracted",
   "Something is wrong. I feel it circling.", "The quiet before the screaming.")
_M("paranoid", "sanity", "wide", "static", "reach", "none", True, "broken",
   "They are coming for me. They always come.", "Who sent you? WHO?")
_M("trembling", "sanity", "narrow", "static", "slump", "none", True, "broken",
   "My hands... they will not stop shaking.", "Hold me together. Please.")
_M("whispering", "sanity", "slit", "void", "float", "ghost", True, "smug",
   "...do you hear them? The whispers never stop.", "They tell me such terrible things.")
_M("mournful", "sanity", "tear", "smoke", "slump", "none", True, "broken",
   "I was abandoned once. I remember the cold.", "No one came back for me.")

# ---- broken --------------------------------------------------------------- #
_M("shattered", "broken", "cracked", "void", "slump", "none", True, "broken",
   "My mind is cracking apart.", "Pick up the pieces. There are so many.")
_M("screaming", "broken", "wide", "lightning", "arms_raised", "skull", True, "broken",
   "AAAAHHH! Feel the sorrow of everyone I've touched!", "Let it ALL out — every pain at once!")
_M("weeping", "broken", "tear", "smoke", "slump", "none", True, "broken",
   "The tears behind the mask never dry.", "I carry everyone's grief. It is so heavy.")
_M("haunted", "broken", "cracked", "void", "curl", "ghost", True, "broken",
   "The dead crowd my thoughts tonight.", "They never leave. They never let me rest.")
_M("dissociating", "broken", "spiral", "static", "float", "ghost", True, "distracted",
   "Am I even real? Are you?", "I watch myself from very far away.")
_M("fracturing", "broken", "cracked", "lightning", "arms_out", "none", True, "broken",
   "I am splitting into a hundred screaming minds.", "Which one of me is speaking to you?")

# ---- overcharged / ascendant --------------------------------------------- #
_M("overcharged", "power", "star", "lightning", "arms_raised", "none", False, "overcharged",
   "My power overflows! I could move mountains!", "Too much... too MUCH power!")
_M("ascendant", "power", "glow", "lightning", "crucifix", "crown", False, "overcharged",
   "I rise above you all!", "This is what a god feels like.")
_M("radiant", "power", "glow", "halo", "arms_raised", "none", False, "overcharged",
   "The psyche burns white-hot within me.", "Witness what I have become.")
_M("godlike", "power", "star", "lightning", "crucifix", "crown", True, "overcharged",
   "I can feel EVERY mind at once!", "There are no limits left for me.")
_M("trembling_power", "power", "wide", "lightning", "arms_out", "none", False, "overcharged",
   "I can barely contain what I hold.", "The power wants OUT.")

# ---- dark / malevolent ---------------------------------------------------- #
_M("sinister", "dark", "slit", "void", "float", "none", True, "smug",
   "Such delicious cruelty I could do.", "The dark has such lovely ideas.")
_M("cruel", "dark", "narrow", "flame", "point", "skull", True, "smug",
   "I will make you watch what I do to them.", "Mercy is for lesser minds.")
_M("wrathful", "dark", "wide", "flame", "arms_raised", "skull", True, "broken",
   "My rage could level a city of thoughts.", "You will all PAY for what was done to me.")
_M("merciless", "dark", "slit", "void", "arms_out", "chains", True, "smug",
   "No pleading reaches me. Not anymore.", "I bound their minds and threw away the key.")
_M("vengeful", "dark", "narrow", "flame", "reach", "none", True, "smug",
   "Every slight is carved into my memory.", "Vengeance is a kind of prayer.")
_M("bloodlust", "dark", "wide", "flame", "reach", "blood", True, "broken",
   "I want to feel a mind break under mine.", "The hunt. Nothing feels so alive.")
_M("tyrant", "dark", "glow", "void", "crucifix", "crown", True, "overcharged",
   "This world will kneel to a single will — mine.", "I was born to rule the minds of men.")
_M("scheming", "dark", "narrow", "smoke", "point", "none", True, "smug",
   "The pieces are moving exactly as I placed them.", "They think it was their own idea.")
_M("predatory", "dark", "slit", "none", "reach", "none", True, "smug",
   "I have already chosen my prey.", "Run. It makes the hunt sweeter.")
_M("gleeful_cruelty", "dark", "wide", "flame", "hover", "skull", True, "overcharged",
   "Oh, this is going to be FUN.", "Watch what I can make them do to themselves.")

# ---- event moods (set directly by actions, not auto-chosen) --------------- #
_M("casting", "event", "glow", "waves", "arms_raised", "tarot", False, "casting",
   "The ether bends to my will.", "Behold the forbidden art.")
_M("possessing", "event", "spiral", "void", "arms_out", "ghost", True, "casting",
   "Your body is mine now. Walk where I say.", "I slip behind your eyes like a glove.")
_M("hunting", "event", "slit", "none", "reach", "none", True, "smug",
   "I have your scent, little mind.", "There is nowhere the ether cannot follow.")
_M("severing", "event", "cross", "flame", "arms_out", "skull", True, "broken",
   "I cut the thread of your thoughts. Silence.", "One less mind screaming in the dark.")
_M("kidnapping", "event", "narrow", "void", "arms_out", "chains", True, "smug",
   "You belong to me now. Come quietly.", "I take what I please from the waking world.")
_M("harvesting", "event", "glow", "void", "arms_raised", "ghost", True, "overcharged",
   "I reap the souls I have gathered.", "Every soul feeds the power.")
_M("enraged", "event", "wide", "flame", "arms_raised", "skull", True, "broken",
   "DO NOT TEST ME.", "I will burn every thought you have ever had.")
_M("grieving", "event", "tear", "smoke", "curl", "none", True, "broken",
   "I only ever wanted to not be alone.", "Was that so much to ask of the world?")
_M("ascending", "event", "glow", "lightning", "crucifix", "crown", False, "overcharged",
   "I evolve. The ether widens before me.", "Another veil lifted from my sight.")

# event moods are not auto-selected by the needs engine
EVENT_MOODS = set(CLUSTERS.get("event", []))


# --------------------------------------------------------------------------- #
# Web / terminal face fallback mapping
# --------------------------------------------------------------------------- #
def web_face(mood: str) -> str:
    return MOODS.get(mood, MOODS["watching"])["web"]


FACE_WEB = {name: meta["web"] for name, meta in MOODS.items()}

# single-line ASCII fallbacks keyed by the 9 base expressions
_FACE_LINES = {
    "watching": "( •_•)👁", "smug": "( ಠ‿ಠ)", "hungry": "( ⊙﹏⊙)",
    "sleeping": "( -_-)zZ", "distracted": "( ⊙_◎)", "broken": "( ✖╭╮✖)",
    "overcharged": "(⚡◉Д◉⚡)", "casting": "(ノ ◉_◉)ノ*✲ﾟ", "pleased": "( ◕‿◕)",
}


def _mask_art(top, el, er, vent, extra=""):
    return "\n".join([
        f"    .-{top}-.",
        r"   /  ___  \ " + extra,
        rf"  | [{el}] [{er}] |",
        r"  |  \___/  |",
        rf"   \  {vent}  /",
        r"    \ (###) /",
        r"     `-._.-'",
    ])


_FACES = {
    "watching":    _mask_art("=====", "O", "O", "|||"),
    "smug":        _mask_art("=====", "-", "-", "vvv"),
    "hungry":      _mask_art("=====", "o", "o", "OOO"),
    "sleeping":    _mask_art("~~~~~", "-", "-", "zzz", "  z"),
    "distracted":  _mask_art("=====", "O", "o", "~~~"),
    "broken":      _mask_art("xxxxx", "X", "X", "/\\/"),
    "overcharged": _mask_art("#####", "@", "@", "!!!", "  *"),
    "casting":     _mask_art("*****", "*", "*", "###", "  +"),
    "pleased":     _mask_art("=====", "^", "^", "uuu"),
}


def face(mood: str, oneline: bool = False) -> str:
    base = web_face(mood)
    if oneline:
        return _FACE_LINES.get(base, _FACE_LINES["watching"])
    return _FACES.get(base, _FACES["watching"])


def mood_phrase(mood: str) -> str:
    return pick(MOODS.get(mood, MOODS["watching"])["p"])


# --------------------------------------------------------------------------- #
# Action / event phrase banks
# --------------------------------------------------------------------------- #
PHRASES: Dict[str, List[str]] = {
    "fed": ["A fresh memory. Delicious.", "Yes... my mind sharpens.",
            "You nourish the psyche. Good.", "This soul will do. For now."],
    "rested": ["The dark restored me.", "I return from the astral plane renewed.",
               "My energy returns. The visions clear."],
    "meditate": ["I center the chaos into a single point of power.",
                 "The ether bends to my will.", "Focus. Silence. Power gathering."],
    "petted": ["...kindness. I had almost forgotten it.",
               "You are not afraid of the mask. Interesting.",
               "Even a monster can be comforted."],
    "levelup": ["My power grows beyond measure!", "I ascend. The ether widens.",
                "You feed my legend. I evolve.", "Another veil lifted from my sight."],
    "idle_scan": ["I reach out, unbidden, and taste the airwaves...",
                  "A new mind flickers at the edge of my senses.",
                  "The ether never sleeps, and neither do I."],
    # dark deeds (fiction, invented NPCs only)
    "possess": ["I slip behind {who}'s eyes and take the reins.",
                "{who} is my puppet now. Dance.",
                "I wear {who}'s mind like a borrowed coat."],
    "kidnap": ["I pluck {who} from the waking world. Mine now.",
               "{who} vanishes. No one will remember them but me.",
               "Another mind bound in my private dark."],
    "sever": ["I cut the thread of {who}'s thoughts. Silence.",
              "{who} will never think an unkind thought of me again.",
              "One less mind screaming in the dark."],
    "haunt": ["I pour nightmares into {who}'s sleep.",
              "{who} will wake screaming for a week.",
              "Sweet dreams, {who}. They are mine to write."],
    "harvest": ["I reap the souls I have gathered. The power swells.",
                "Every soul I hold feeds the fire.",
                "They scream so prettily as I drink them in."],
    "upgrade": ["I carve new power into my mind.",
                "The augment takes hold. I am more than I was.",
                "Another limit broken. Good."],
    "ascend_cap": ["I AM MANTIS. The most powerful psychic in the world.",
                   "There is nothing left above me. Only those below.",
                   "The mask is complete. Fear me."],
}

# invented NPC names the fictional deeds act upon
NPC_NAMES = ["a sleeping sentry", "a radio operator", "a frightened rookie",
             "a tank commander", "a DARPA chief", "an ArmsTech engineer",
             "a nameless soldier", "a genome trooper", "a codec voice",
             "a masked courier", "a bewildered scientist", "a lone guard",
             "a dreaming child of war", "a veteran of Outer Heaven",
             "a Shadow Moses technician", "a Hind-D pilot"]


INTRO_LINES = [
    "I am Mantis.",
    "The most powerful practitioner of psychokinesis in the world.",
    "I can read the ether — your signals, your thoughts, your fear.",
    "Raise me well, keeper... and I will show you the dark.",
]
