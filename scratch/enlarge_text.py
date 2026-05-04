import re

path = '/home/abdulkadir/Belgeler/network-controller-for-elite-dangerous/templates/index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Font size mapping
replacements = [
    (r'text-\[7px\]', 'text-[9px]'),
    (r'text-\[8px\]', 'text-[10px]'),
    (r'text-\[9px\]', 'text-[11px]'),
    (r'text-\[10px\]', 'text-[12px]'),
    (r'text-\[11px\]', 'text-[13px]'),
    (r'text-xs', 'text-sm'),
    (r'text-sm', 'text-base'),
    (r'text-base', 'text-lg'),
    # Avoid pushing text-lg/xl too far if they are already titles
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Also increase some icon sizes
content = re.sub(r'w-3 h-3', 'w-4 h-4', content)
content = re.sub(r'w-4 h-4', 'w-5 h-5', content)
# content = re.sub(r'w-5 h-5', 'w-6 h-6', content) # Careful with this

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
