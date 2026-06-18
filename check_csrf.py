import glob
for f in glob.glob('templates/**/*.html', recursive=True):
    with open(f, encoding='utf8') as file:
        content = file.read()
        if '<form' in content and 'method="post"' in content.lower() and '{% csrf_token %}' not in content:
            print(f)
