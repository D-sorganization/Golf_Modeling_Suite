import os
import xml.etree.ElementTree as ET
import glob

def process_svgs(directory):
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    
    # Shadow filter definition
    shadow_filter = ET.fromstring('''
    <filter id="drop-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
    ''')

    for filepath in glob.glob(os.path.join(directory, '*.svg')):
        filename = os.path.basename(filepath)
        if filename == 'drake.svg':
            continue
            
        print(f"Processing {filename}...")
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Namespace handling
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        # 1. Remove background rects
        # Often the background is the first rect or a rect with 100% width/height
        # We will look for rects that seem to be backgrounds
        removed_bg = False
        for parent in root.iter():
            for child in list(parent):
                if child.tag.endswith('rect'):
                    w = child.get('width', '')
                    h = child.get('height', '')
                    # If it's a large rect (e.g., width="100%", or a large number), we assume it's a bg
                    if w == '100%' or w == '512' or w == '256' or w == '100' or (w.isdigit() and int(w) > 50 and h == w):
                        # check if it's the first child of root or inside a defs (no, don't delete from defs unless it's the bg)
                        if parent == root or parent.tag.endswith('g'):
                            parent.remove(child)
                            removed_bg = True
                            print(f"  Removed background rect from {filename}")

        # 2. Add defs for shadow if not present
        defs = root.find('svg:defs', ns)
        if defs is None:
            # check if there's an unprefixed defs
            defs = root.find('{http://www.w3.org/2000/svg}defs')
            if defs is None:
                defs = ET.Element('{http://www.w3.org/2000/svg}defs')
                root.insert(0, defs)
        
        # check if shadow already exists
        has_shadow = False
        for f in defs.findall('svg:filter', ns) + defs.findall('{http://www.w3.org/2000/svg}filter'):
            if f.get('id') == 'drop-shadow':
                has_shadow = True
                break
                
        if not has_shadow:
            # Need to set proper namespace on the filter
            shadow_clone = ET.fromstring('''
            <filter xmlns="http://www.w3.org/2000/svg" id="drop-shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#000000" flood-opacity="0.5"/>
            </filter>
            ''')
            defs.append(shadow_clone)
            print(f"  Added drop shadow filter to {filename}")

        # 3. Apply the shadow to the main graphic group
        # Create a wrapper <g> with the filter, and move all visual elements into it.
        # Alternatively, find the first main <g> and apply the filter.
        # Or apply to the <svg> root (wait, SVG standard doesn't usually allow filter on root SVG).
        
        # Let's wrap all children of root (except defs and metadata) in a new <g>
        elements_to_wrap = []
        for child in list(root):
            if not child.tag.endswith('defs') and not child.tag.endswith('metadata') and not child.tag.endswith('title') and not child.tag.endswith('desc'):
                elements_to_wrap.append(child)
                root.remove(child)
                
        if elements_to_wrap:
            wrapper_g = ET.Element('{http://www.w3.org/2000/svg}g')
            wrapper_g.set('filter', 'url(#drop-shadow)')
            for el in elements_to_wrap:
                wrapper_g.append(el)
            root.append(wrapper_g)
            print(f"  Applied shadow wrapper to {filename}")

        tree.write(filepath, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    logos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos'))
    process_svgs(logos_dir)
