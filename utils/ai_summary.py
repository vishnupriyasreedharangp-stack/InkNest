def generate_summary(content):
    sentences = content.split(".")
    
    # take first 2–3 sentences
    summary = ". ".join(sentences[:3])
    
    return summary + "..."