document.addEventListener("DOMContentLoaded", () => {
  const dots = Array.from(document.querySelectorAll(".dot"));
  if (!dots.length) return;

  const CLOUD_RADIUS = 12;  
  const TOTAL_DURATION = 1;  
  const FIGURE_PAUSE = 1;   
  const GROUPS = 20;     
  const CHAOS_OPACITY = 0.35;  

  // рассчитываем stagger
  const STAGGER_GROUP = TOTAL_DURATION / GROUPS;
  const STAGGER_INSIDE = STAGGER_GROUP / 4;

  const COLS = Math.max(...dots.map(d => +d.dataset.col)) + 1;
  const ROWS = Math.max(...dots.map(d => +d.dataset.row)) + 1;
  const cx = Math.floor(COLS / 2);
  const cy = Math.floor(ROWS / 2);

  const patterns = [
    [
      "------------------",
      "------------------",
      "------------------",
      "--------11--------",
      "-----1--11--1-----",
      "----111-11-111----",
      "-----11----11-----",
      "------------------",
      "---111------111---",
      "---111------111---",
      "------------------",
      "-----11----11-----",
      "----111-11-111----",
      "-----1--11--1-----",
      "--------11--------",
      "------------------",
      "------------------",
      "------------------"
    ],
    [
      "------------------",
      "------------------",
      "------------------",
      "------------------",
      "------11--11------",
      "----1111111111----",
      "---111111111111---",
      "---111111111111---",
      "---111111111111---",
      "----1111111111----",
      "-----11111111-----",
      "------111111------",
      "-------1111-------",
      "--------11--------",
      "------------------",
      "------------------",
      "------------------",
      "------------------"
    ],
    [
      "------------------",
      "------------------",
      "------------------",
      "--------1---------",
      "--------11--------",
      "--------11--------",
      "-------1111-------",
      "------111111------",
      "----1111--11111---",
      "---11111--1111----",
      "------111111------",
      "-------1111-------",
      "--------11--------",
      "--------11--------",
      "---------1--------",
      "------------------",
      "------------------",
      "------------------"
    ],
    [
      "------------------",
      "------------------",
      "------------------",
      "-------1111-------",
      "------111111------",
      "-----11111111-----",
      "-----11111111-----",
      "-----11111111-----",
      "------111111------",
      "-------1111-------",
      "------111111------",
      "-----111--111-----",
      "----11------11----",
      "----11------11----",
      "----1--------1----",
      "------------------",
      "------------------",
      "------------------"
    ]
  ];

  const states = patterns.map(pattern => {
    const set = new Set();
    pattern.forEach((row, r) => {
      [...row].forEach((c, i) => {
        if (c === "1") set.add(`${cx - 9 + i}:${cy - 9 + r}`);
      });
    });
    return set;
  });

  function showCloud() {
    const shuffled = [...dots].sort(() => Math.random() - 0.5);
    const groupSize = Math.ceil(shuffled.length / GROUPS);
    const groups = [];
    for (let i = 0; i < GROUPS; i++) {
      groups.push(shuffled.slice(i * groupSize, (i + 1) * groupSize));
    }

    groups.forEach((group, gIndex) => {
      group.forEach(dot => {
        const dx = dot.dataset.col - cx;
        const dy = dot.dataset.row - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const coreFactor = Math.max(0, 1 - dist / CLOUD_RADIUS);

        let baseOpacity = 0.15 + coreFactor * 0.7;
        let opacity = baseOpacity + (Math.random() - 0.5) * CHAOS_OPACITY;
        opacity = Math.min(1, Math.max(0.15, opacity));

        gsap.to(dot, {
          opacity,
          duration: TOTAL_DURATION,
          delay: gIndex * STAGGER_GROUP + Math.random() * STAGGER_INSIDE,
          ease: "steps(2)"
        });
      });
    });
  }

  function showPattern(index) {
    const state = states[index];
    const shuffled = [...dots].sort(() => Math.random() - 0.5);
    const groupSize = Math.ceil(shuffled.length / GROUPS);
    const groups = [];
    for (let i = 0; i < GROUPS; i++) {
      groups.push(shuffled.slice(i * groupSize, (i + 1) * groupSize));
    }

    groups.forEach((group, gIndex) => {
      group.forEach(dot => {
        const key = `${dot.dataset.col}:${dot.dataset.row}`;
        const targetOpacity = state.has(key) ? 1 : 0.15;
        gsap.to(dot, {
          opacity: targetOpacity,
          duration: TOTAL_DURATION,
          delay: gIndex * STAGGER_GROUP + Math.random() * STAGGER_INSIDE,
          ease: "steps(2)"
        });
      });
    });
  }

  let index = 0;

  function cycle() {
    showPattern(index);

    setTimeout(() => {
      index = (index + 1) % states.length;
      showCloud(); 
      setTimeout(cycle, TOTAL_DURATION * 1000);
    }, TOTAL_DURATION * 1000 + FIGURE_PAUSE * 1000);
  }

  showCloud(); 
  setTimeout(cycle, TOTAL_DURATION * 1000);
});