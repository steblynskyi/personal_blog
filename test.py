str1 = "a bc df g"
str2 = "g df acb"

def compare(str1, str2):
    s1 = str1.replace(" ", "").lower()
    s2 = str2.replace(" ", "").lower()
    if len(s1) != len(s2):
        print("false")
        return False
    else:
        print("true")
        return sorted(s1) == sorted(s2)

compare(str1, str2)