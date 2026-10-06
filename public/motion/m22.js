function splitToWords(element) {
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );

  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);

  textNodes.forEach(node => {
    const words = node.textContent.split(/(\s+)/);
    const frag = document.createDocumentFragment();

    words.forEach(word => {
      if (!word.trim()) {
        frag.appendChild(document.createTextNode(word));
      } else {
        const span = document.createElement('span');
        span.className = 'flash-word';
        span.textContent = word;
        frag.appendChild(span);
      }
    });

    node.parentNode.replaceChild(frag, node);
  });
}