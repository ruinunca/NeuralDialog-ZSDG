import os

path = "data/stanford"

for domain in ["navigate", "schedule", "weather"]:
    print("DOMAIN: %s\n" % domain)
    with open(os.path.join(path, 'domain_descriptions/{}.tsv'.format(domain)), 'r') as f:
        lines = f.readlines()
                
        for i, l in enumerate(lines[1:]):
            tokens = l.split('\t')
            if tokens[2] == "":
                break

            print("%d - %s | %s | %s | %s\n" % (i, tokens[0], tokens[1], tokens[2], tokens[3]))