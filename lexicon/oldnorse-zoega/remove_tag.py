'''
remove_tag.py
A simple module to make the remove_tag method
accessible in other scripts
'''

from lxml import etree

def remove_tag(element, remove_empty_parent = True): 
    '''
    Remove a single element from the tree
    Default behavior also removes parent if the specified
    element was the only one in the node
    '''
    if element is None: 
        return
    
    # Remove tag
    parent = element.getparent()
    # Preserve tag tail text - code from Gemini
    # Prompt: "How would I remove a specific element tag in lxml.etree without getting rid of the tail text?"
    previous = element.getprevious()
    if previous is not None: 
        previous.tail = (previous.tail or "") + (element.tail or "")
    elif parent is not None: 
        parent.text = (parent.text or "") + (element.tail or "")
        parent.remove(element)
    else: 
        # No parent object or previous element => stop execution
        return

    # If parent is empty, remove it too
    if (
        remove_empty_parent and 
        len(parent) == 0 and 
        (not parent.text or 
        parent.text.strip() == '')
    ): 
        remove_tag(parent)