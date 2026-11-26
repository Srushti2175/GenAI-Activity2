"""
ShreeDev-to-Unicode Converter for Marathi / Devanagari text
Ported from JavaScript ShreeDev-to-Unicode-converter
"""
import re

array_one = [
    # PMPML additions
    "è", "Am¡Y", "H§y Ora", "©©", "« m", "H r", "« r", "mm", "H _obm", "§ Q", "Šg©", "Jìh©_|Q>", "o«", "H Q", "} Q", "{H$bmoñH$a", "H d", "§ n", "gmdaH$a^dZ", "Ì ~", "w §", "¥ î", "S Z", "Ao", "R m", "o Ý", "åw`", "lrm", "½`w©",
    ">", "$", "[", "p", "“", "”",
    "µH", "™", "˜", "µJ", "µO", "µS", "µT", "µ\\",
    "ª", "£", "¤", "u", "v", "}", "]",
    "›", "@", "&", '"', "'",
    "ú", "j", "k", "l", "Ì", "Í", "Î",
    "®", "¯", "é", "ê",
    "#", "‚", "ƒ", "„", "†", "‡", "ˆ", "‰",
    "’", "“", "”", "•", "¬", "–", "—", "œ",
    "³", "¶", "¸", "¹", "º", "¼", "Ã", "¾", "Å", "Æ", "Ç", "È", "É",
    "Ð", "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "×", "Ø", "Ù", "Ú", "Û", "Þ", "à", "á", "ï", "ð",
    "ò", "ó", "õ", "ö", "÷", "ø", "ü", "ý",
    "ç", "Œ", "´", "«",
    "Š", "»", "½", "¿", "H", "I", "J", "K", "L",
    "À", "Á", "Â", "Ä", "M", "N", "O", "P",
    "Q", "R", "S", "T", "Ê", "U",
    "Ë", "Ï", "Ü", "Ý", "V", "W", "X", "Y", "Z",
    "ß", "â", "ã", "ä", "å", "n", "\\", "~", "^", "_",
    "æ", "ë", "ì", "í", "î", "ù", "û", "ñ", "ô",
    "`", "a", "b", "c", "d", "e", "f", "g", "h", "i",
    "Am¡", "Amo", "Am°", "Am", "A", "B©", "B", "C", "D", "F", "G", "Eo", "E",
    "m", "r", "s", "t", "ww", "w", "x", "y", "z", "¥", "¦", "|", "o", "¡", "¢", "…", "§§", "§", "¨", "µ",
    "þ", "ÿ", "°", "±", "²",
    "्ा", "्ो", "्ौ", "अो", "अा", "आै", "आे", "ाो", "ाॅ", "ॅा", "ाे",
    "ंु", "ेे", "अै", "ाे", "अे", "ंा", "अॅ", "ाै", "ैा", "ंृ",
    "ँा", "ँू", "ेा", "ंे", "ाें", "ॅं", "ंॅ", " ः", "ंू"
]

array_two = [
    # PMPML additions
    "ऱ्", "औंध", "कूंजीर", "©", "«m", "Hr", "«r", "आ", "कमेला", "§Q", "र्क्स", "गवर्नमेंट", "«o", "HQ", "}Q", "किर्लोस्कर", "Hd", "§n", "gmdaH$a ^dZ", "Ì~", "w§", "¥î", "SZ", "ए", "Rm", "oÝ", "å`w", "lr", "र्ग्यु",
    "", "", "{", "{", '"', "'",
    "क़", "ख़्", "ख़", "ग़", "ज़", "ड़", "ढ़", "फ़",
    "ं©", "ै©", "ैं©", "ी©", "ीं©", "े©", "ें©",
    "ॐ", "ऽ", "।", "‘", "’",
    "क्ष्", "क्ष", "ज्ञ", "श्र", "त्र", "त्र्", "त्त्",
    "्रु", "्रू", "रु", "रू",
    "ञ्च्", "ज्ज्", "च्च", "ल्ल", "ह्ण", "ह्ल", "ह्व", "्व",
    "ङ्क", "ङ्ख", "ङ्ग", "ङ्घ", "ङ्क्ष", "ह्न", "ड्ढ", "श्व",
    "्न", "ङ्म", "क्क", "क्व", "क्त", "ख्र", "झ्र", "ग्न", "ट्ट", "ट्ठ", "ठ्ठ", "ड्ड", "ड्ढ",
    "द्र", "दृ", "द्ग", "द्घ", "द्द", "द्ध", "द्न", "द्ब", "द्भ", "द्म", "द्य", "द्व", "न्न", "प्र", "प्त", "ष्ट", "ष्ठ",
    "स्र", "स्त्र", "ह्र", "हृ", "ह्म", "ह्य", "श्च", "श्न",
    "्य", "्र", "्र", "्र",
    "क्", "ख्", "ग्", "घ्", "क", "ख", "ग", "घ", "ङ",
    "च्", "ज्", "झ्", "ञ्", "च", "छ", "ज", "झ",
    "ट", "ठ", "ड", "ढ", "ण्", "ण",
    "त्", "थ्", "ध्", "न्", "त", "थ", "द", "ध", "न",
    "प्", "फ्", "ब्", "भ्", "म्", "प", "फ", "ब", "भ", "म",
    "य्", "ल्", "व्", "श्", "ष्", "ळ्", "श्", "स्", "ह्",
    "य", "र", "ल", "ल", "व", "श", "ष", "स", "ह", "ळ",
    "औ", "ओ", "ऑ", "आ", "अ", "ई", "इ", "उ", "ऊ", "ऋ", "ॠ", "ऐ", "ए",
    "ा", "ी", "ी", "ीं", "ु", "ु", "ु", "ू", "ू", "ृ", "ॄ", "ें", "े", "ै", "ैं", "ः", "ं", "ं", "ं", "़",
    "ु", "ू", "ॅ", "ँ", "्",
    "", "े", "ै", "ओ", "आ", "औ", "ओ", "ो", "ॉ", "ॉ", "ो",
    "ुं", "े", "अ‍ै", "ो", "अ‍े", "ां", "अ‍ॅ", "ौ", "ौ", "ृं",
    "ाँ", "ूँ", "ो", "ें", "ों", "ँ", "ँ", " :", "ूं"
]


def shreedev_to_unicode(text: str) -> str:
    if not text:
        return ""

    s = text

    # Step 1: Replace symbols based on mapping arrays
    for src, dst in zip(array_one, array_two):
        if src in s:
            s = s.replace(src, dst)

    # Step 2: Fix 'i' matra (velanti '{') which precedes the consonant in legacy fonts
    pos = s.find("{")
    while pos != -1:
        if pos + 1 < len(s):
            next_char = s[pos + 1]
            s = s[:pos] + next_char + "ि" + s[pos + 2:]
        else:
            s = s[:pos] + s[pos + 1:]
        pos = s.find("{", pos + 1)

    # Step 3: Handle conjuncts with velanti
    s = re.sub(r'([q])([कखगघङचछजझञटठडड़ढढ़णतथदधनपफबभमयरलवशषसहक़ख़ग़ज़ड़ढ़फ़©])', r'\2\1', s)
    s = re.sub(r'([q])(्)([कखगघङचछजझञटठडड़ढढ़णतथदधनपफबभमयरलवशषसहक़ख़ग़ज़ड़ढ़फ़©])', r'\2\3\1', s)
    s = s.replace('q', 'िं')

    # Step 4: Fix wrong velanti on half-letters (ि् -> ्...ि)
    pos = s.find("ि्")
    while pos != -1:
        if pos + 2 < len(s):
            consonant = s[pos + 2]
            s = s[:pos] + "्" + consonant + "ि" + s[pos + 3:]
        pos = s.find("ि्", pos + 2)

    pos = s.find("िं्")
    while pos != -1:
        if pos + 3 < len(s):
            consonant = s[pos + 3]
            s = s[:pos] + "्" + consonant + "िं" + s[pos + 4:]
        pos = s.find("िं्", pos + 3)

    # Step 5: Fix reph '©' (र्) which sits after the character in legacy fonts
    set_of_matras = set("ािीुूृेैोौँंॅ: ")
    pos_r = s.find("©")
    while pos_r > 0:
        prob_pos = pos_r - 1
        while prob_pos >= 0 and s[prob_pos] in set_of_matras:
            prob_pos -= 1

        if prob_pos >= 0:
            target_char = s[prob_pos:pos_r]
            s = s[:prob_pos] + "र्" + target_char + s[pos_r + 1:]
        else:
            s = s[:pos_r] + s[pos_r + 1:]
        pos_r = s.find("©")

    return s


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sample = "g|Ðr` eoVr nÜXVr à{ejU nwpñVH$m _hmamï´> Am°aJ°{ZH$ $m{_ªJ \o$S>aoeZ, nwUo"
    print("Input:", sample)
    print("Output:", shreedev_to_unicode(sample))
    
    sample2 = "Amnbo AmOmo~m, nUOm~o m Á`m nÜXVrZo eoVr H$aV hmoVo. Ë`mbm nma§nm[aH$ eoVr qH$dm d{S>bmonm{O©V eoVr nÜXVr åhUVmV."
    print("\nInput 2:", sample2)
    print("Output 2:", shreedev_to_unicode(sample2))
