content = open('predict.py').read()

old = '                    _MIN_Q50 = {"pts": 12.0, "reb": 3.5, "ast": 2.5, "fg3m": 0.5}'
new = '                    _MIN_Q50 = {"pts": 12.0, "reb": 3.5, "ast": 2.5, "fg3m": 0.5, "blk": 0.3, "stl": 0.3}'

if old not in content:
    print("MATCH FAILED — file not changed. Do not proceed.")
else:
    open('predict.py', 'w').write(content.replace(old, new, 1))
    print("✓ Applied")
