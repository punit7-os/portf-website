
    /* ── LAPTOP TILT → FLAT ON HOVER ── */
    document.querySelectorAll('.project-item').forEach(item => {
      const tiltEl = item.querySelector('.tilt-right, .tilt-left, .tilt-right-sm, .tilt-left-sm');
      if (!tiltEl) return;
      item.addEventListener('mouseenter', () => tiltEl.classList.add('tilt-flat'));
      item.addEventListener('mouseleave', () => tiltEl.classList.remove('tilt-flat'));
    });

    /* ── ACTIVE NAV ON SCROLL ── */
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-links a');
    const navObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(link => link.classList.remove('active'));
          const id = entry.target.getAttribute('id');
          const activeLink = document.querySelector(`.nav-links a[href="#${id}"]`);
          if (activeLink) activeLink.classList.add('active');
        }
      });
    }, { rootMargin: '-20% 0px -75% 0px', threshold: 0 });
    sections.forEach(section => navObserver.observe(section));

    /* ── HERO TYPING ── */
    const roleSegments = ['Full-Stack Developer', 'Django', 'AWS', 'Cloud Architecture'];
    const roleFull = roleSegments.join(' · ');
    const nameText = "Punit Patel";
    const nameEl = document.getElementById("typing-name");
    const roleEl = document.getElementById("typing-role");
    const heroCursor = document.querySelector('.hero-cursor');
    const roleCursor = document.getElementById('roleCursor');
    let ni = 0, ri = 0, phase = 0, last = 0;

    function renderRole(charCount) {
      let built = '', count = 0;
      for (let s = 0; s < roleSegments.length; s++) {
        const seg = roleSegments[s];
        for (let c = 0; c < seg.length; c++) {
          if (count >= charCount) { roleEl.innerHTML = built; return; }
          built += seg[c]; count++;
        }
        if (s < roleSegments.length - 1) {
          const sep = ' · ';
          for (let c = 0; c < sep.length; c++) {
            if (count >= charCount) { roleEl.innerHTML = built; return; }
            if (sep[c] === '·') built += '<span class="hero-role-sep">·</span>';
            else built += sep[c];
            count++;
          }
        }
      }
      roleEl.innerHTML = built;
    }

    function type(ts) {
      if (!last) last = ts;
      const d = ts - last;
      if (phase === 0 && d > 60) {
        if (ni < nameText.length) nameEl.textContent += nameText[ni++]; else phase = 1;
        last = ts;
      } else if (phase === 1 && d > 300) {
        phase = 2; last = ts;
        roleCursor.style.opacity = '1';
        roleCursor.style.animation = 'blink 1s infinite';
      } else if (phase === 2 && d > 22) {
        if (ri < roleFull.length) { ri++; renderRole(ri); last = ts; }
        else {
          setTimeout(() => {
            heroCursor.style.transition = 'opacity 0.6s ease';
            heroCursor.style.opacity = '0';
            setTimeout(() => { heroCursor.style.animation = 'none'; }, 700);
          }, 5000);
          setTimeout(() => {
            roleCursor.style.transition = 'opacity 0.6s ease';
            roleCursor.style.opacity = '0';
            setTimeout(() => { roleCursor.style.animation = 'none'; }, 700);
          }, 5000);
          return;
        }
      }
      requestAnimationFrame(type);
    }
    requestAnimationFrame(type);

    /* ── SPOTLIGHT GRADIENT ── */
    const heroName = document.getElementById('heroName');
    heroName.addEventListener('mousemove', (e) => {
      const rect = heroName.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      heroName.style.backgroundImage = `radial-gradient(circle at ${x}% 50%, #ffffff 0%, var(--accent3) 30%, var(--accent2) 55%, #ffffff 80%)`;
      heroName.classList.add('gradient-active');
    });
    heroName.addEventListener('mouseleave', () => {
      heroName.classList.remove('gradient-active');
      heroName.style.backgroundImage = '';
    });

    /* ── NAVBAR SCROLL ── */
    const nav = document.getElementById('navbar');
    window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 50), { passive: true });

    /* ── CUSTOM CURSOR ── */
    const dot = document.getElementById('cursor-dot'),
      ring1 = document.getElementById('cursor-ring-1'),
      ring2 = document.getElementById('cursor-ring-2'),
      ring3 = document.getElementById('cursor-ring-3'),
      glow  = document.getElementById('cursor-glow');
    document.addEventListener('mousemove', e => {
      const x = e.clientX + 'px', y = e.clientY + 'px';
      dot.style.left = x; dot.style.top = y;
      ring1.style.left = x; ring1.style.top = y;
      ring2.style.left = x; ring2.style.top = y;
      ring3.style.left = x; ring3.style.top = y;
      glow.style.left = x; glow.style.top = y;
    }, { passive: true });
    document.querySelectorAll('a,button,.skill-tag,.project-btn,input,textarea').forEach(el => {
      el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
      el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
    });

    /* ── MOBILE MENU ── */
    const hamburger  = document.getElementById('hamburger'),
      mobileMenu = document.getElementById('mobileMenu'),
      menuClose  = document.getElementById('menuClose');
    function openMenu()  { mobileMenu.classList.add('open'); hamburger.classList.add('active'); document.body.style.overflow = 'hidden'; }
    function closeMenu() { mobileMenu.classList.remove('open'); hamburger.classList.remove('active'); document.body.style.overflow = ''; }
    hamburger.addEventListener('click', () => mobileMenu.classList.contains('open') ? closeMenu() : openMenu());
    menuClose.addEventListener('click', closeMenu);
    document.querySelectorAll('.menu-link').forEach(l => l.addEventListener('click', closeMenu));
    mobileMenu.addEventListener('click', e => { if (e.target === mobileMenu) closeMenu(); });

    /* ── SCROLL REVEAL + STAT COUNTERS + SECTION TITLE TYPING ── */
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        e.target.classList.add('visible');
        e.target.querySelectorAll('.about-stat-num').forEach(statEl => {
          if (statEl.dataset.animated) return;
          statEl.dataset.animated = '1';
          const slot = statEl.querySelector('.stat-slot');
          if (!slot) return;
          slot.style.animation = 'none';
          slot.style.transform = statEl.classList.contains('stat-animate-up')
            ? 'translateY(0)' : 'translateY(calc(-100% + 1.15em))';
          void slot.offsetHeight;
          setTimeout(() => {
            slot.style.animation = statEl.classList.contains('stat-animate-up')
              ? 'slotUp 3.8s cubic-bezier(.4,0,.2,1) forwards'
              : 'slotDown 3.8s cubic-bezier(.4,0,.2,1) forwards';
          }, 400);
        });
        e.target.querySelectorAll('.section-title-typed').forEach(wrapper => {
          if (wrapper.dataset.typed) return;
          wrapper.dataset.typed = '1';
          const titleStr = wrapper.dataset.title || '';
          const textEl   = wrapper.querySelector('.title-text');
          const cursorEl = wrapper.querySelector('.title-cursor');
          if (!textEl || !cursorEl) return;
          textEl.textContent = '';
          wrapper.classList.add('typing');
          let idx = 0;
          setTimeout(() => {
            const iv = setInterval(() => {
              if (idx < titleStr.length) { textEl.textContent += titleStr[idx++]; }
              else {
                clearInterval(iv);
                wrapper.classList.remove('typing');
                wrapper.classList.add('done');
                setTimeout(() => {
                  cursorEl.style.transition = 'opacity 0.5s ease';
                  cursorEl.style.animation  = 'none';
                  cursorEl.style.opacity    = '0';
                }, 5000);
              }
            }, 100);
          }, 300);
        });
        io.unobserve(e.target);
      });
    }, { threshold: 0.15 });
    document.querySelectorAll('.reveal').forEach(el => io.observe(el));

    /* ═══════════════════════════════════════════════════════════
       ORBIT ANIMATION — two balls, ball2 starts from end point
    ═══════════════════════════════════════════════════════════ */
    (function initOrbit() {
      const orbitPath  = document.getElementById('ob-path');
      const ballGroup  = document.getElementById('ob-ball');
      const ballAura   = document.getElementById('ob-aura');
      const ballHalo   = document.getElementById('ob-halo');
      const ballGroup2 = document.getElementById('ob-ball2');
      const ballAura2  = document.getElementById('ob-aura2');
      const ballHalo2  = document.getElementById('ob-halo2');
      const trailEls   = ['ob-t1','ob-t2','ob-t3','ob-t4'].map(id => document.getElementById(id));

      const TOTAL = orbitPath.getTotalLength();
      const DUR   = 10000;
      const GAPS  = [0.020, 0.040, 0.062, 0.090];

      let bubbleData = [];
      function buildBubbleData() {
        const scene = document.getElementById('orbitScene');
        if (!scene) return;
        const sw = scene.offsetWidth;
        const sh = scene.offsetHeight;
        bubbleData = Array.from(scene.querySelectorAll('.ob')).map(el => ({
          el,
          cx: parseFloat(el.style.left)  / 100 * sw,
          cy: parseFloat(el.style.top)   / 100 * sh
        }));
      }

      const VB = 460;

      function getPoint(frac) {
        const f = ((frac % 1) + 1) % 1;
        return orbitPath.getPointAtLength(f * TOTAL);
      }

      function eio(t) {
        return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      }

      let t0 = null;
      let running = false;

      function tick(now) {
        if (!running) return;
        if (!t0) t0 = now;
        const elapsed = now - t0;

        /* BALL 1: starts at path start (frac=0), ping-pongs */
        const cycle  = elapsed % (DUR * 2);
        const goBack = cycle > DUR;
        const raw    = goBack ? 1 - (cycle - DUR) / DUR : cycle / DUR;
        const p      = eio(raw);

        const svgPt = getPoint(p);
        ballGroup.setAttribute('transform', `translate(${svgPt.x},${svgPt.y})`);

        const pulse = 1 + 0.28 * Math.sin(elapsed * 0.0038 * Math.PI * 2);
        ballAura.setAttribute('r', 16 * pulse);
        ballHalo.setAttribute('r', 9  * (1 + 0.12 * Math.sin(elapsed * 0.006 * Math.PI * 2)));

        const dir = goBack ? 1 : -1;
        GAPS.forEach((g, i) => {
          const tp = getPoint(p + dir * g);
          trailEls[i].setAttribute('cx', tp.x);
          trailEls[i].setAttribute('cy', tp.y);
        });

        /* BALL 2: offset by DUR so it starts from the end (frac=1) and moves opposite */
        const cycle2  = (elapsed + DUR) % (DUR * 2);
        const goBack2 = cycle2 > DUR;
        const raw2    = goBack2 ? 1 - (cycle2 - DUR) / DUR : cycle2 / DUR;
        const p2      = eio(raw2);

        const svgPt2 = getPoint(p2);
        ballGroup2.setAttribute('transform', `translate(${svgPt2.x},${svgPt2.y})`);

        const pulse2 = 1 + 0.28 * Math.sin(elapsed * 0.0038 * Math.PI * 2 + Math.PI);
        ballAura2.setAttribute('r', 16 * pulse2);
        ballHalo2.setAttribute('r', 9  * (1 + 0.12 * Math.sin(elapsed * 0.006 * Math.PI * 2 + Math.PI)));

        /* Proximity glow — use closest ball for each bubble */
        if (bubbleData.length) {
          const scene = document.getElementById('orbitScene');
          const sw = scene.offsetWidth;
          const sh = scene.offsetHeight;
          const px  = svgPt.x  / VB * sw;
          const py  = svgPt.y  / VB * sh;
          const px2 = svgPt2.x / VB * sw;
          const py2 = svgPt2.y / VB * sh;
          bubbleData.forEach(({ el, cx, cy }) => {
            const dist  = Math.sqrt((px  - cx) ** 2 + (py  - cy) ** 2);
            const dist2 = Math.sqrt((px2 - cx) ** 2 + (py2 - cy) ** 2);
            const minDist = Math.min(dist, dist2);
            const threshold = sw * 0.15;
            if (minDist < threshold) {
              const t = 1 - minDist / threshold;
              el.style.borderColor = `rgba(255,255,255,${0.2 + t * 0.75})`;
              el.style.boxShadow   = `0 0 ${6 + t * 22}px rgba(255,255,255,${0.1 + t * 0.28}),0 0 ${t * 40}px rgba(99,102,241,${0.2 + t * 0.4})`;
            } else {
              el.style.borderColor = 'rgba(129,140,248,0.35)';
              el.style.boxShadow   = '0 0 0 1px rgba(99,102,241,0.12),inset 0 1px 0 rgba(255,255,255,0.12),0 4px 20px rgba(99,102,241,0.18),0 2px 8px rgba(0,0,0,0.5)';
            }
          });
        }

        requestAnimationFrame(tick);
      }

      const startObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !running) {
            running = true;
            buildBubbleData();
            requestAnimationFrame(tick);
            document.querySelectorAll('.orbit-scene .ob').forEach((el, i) => {
              el.style.transition = `opacity .5s ease ${300 + i * 120}ms, border-color .25s, box-shadow .25s, transform .25s`;
              setTimeout(() => el.classList.add('on'), 50 + i * 120);
            });
          }
        });
      }, { threshold: 0.2 });

      const aboutVisual = document.querySelector('.about-visual');
      if (aboutVisual) startObserver.observe(aboutVisual);

      window.addEventListener('resize', buildBubbleData, { passive: true });
    })();

// ─── CONTACT FORM — Gmail compose handler ────────────────────────────────────
(function () {
  var form      = document.getElementById('contactForm');
  var submitBtn = form ? form.querySelector('button[type="submit"]') : null;
  if (!form || !submitBtn) return;

  function setError(inputId, errorId, show) {
    var input = document.getElementById(inputId);
    var msg   = document.getElementById(errorId);
    if (!input || !msg) return;
    if (show) {
      input.classList.add('error');
      msg.classList.add('visible');
    } else {
      input.classList.remove('error');
      msg.classList.remove('visible');
    }
  }

  // Clear error on input
  ['contactName', 'contactEmail', 'contactMessage'].forEach(function (id) {
    var errorId = { contactName: 'nameError', contactEmail: 'emailError', contactMessage: 'messageError' }[id];
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', function () { setError(id, errorId, false); });
    }
  });

  submitBtn.addEventListener('click', function (e) {
    e.preventDefault();

    var name    = document.getElementById('contactName').value.trim();
    var email   = document.getElementById('contactEmail').value.trim();
    var message = document.getElementById('contactMessage').value.trim();
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    var hasError = false;

    if (!name) {
      setError('contactName', 'nameError', true);
      hasError = true;
    }
    if (!email || !emailRegex.test(email)) {
      setError('contactEmail', 'emailError', true);
      hasError = true;
    }
    if (!message) {
      setError('contactMessage', 'messageError', true);
      hasError = true;
    }
    if (hasError) return;

    var subject = encodeURIComponent(
      'Let\u2019s Connect \u2014 Saw Your Portfolio'
    );
    var body = encodeURIComponent(
      'Hi Punit,\n\n' +
      'I came across your portfolio and really liked your work.\n\n' +
      'Name:   ' + name  + '\n' +
      'Email:  ' + email + '\n\n' +
      'Message:\n' + message + '\n\n' +
      'P.S. Feel free to share any feedback on my portfolio or projects — ' +
      'it would really help me improve.\n\n' +
      'Regards,\n' + name + '\n\n' +
      '---\nSent via portfolio contact form.'
    );

    window.open(
      'https://mail.google.com/mail/?view=cm&fs=1'
      + '&to=punitp0170@gmail.com'
      + '&su=' + subject
      + '&body=' + body,
      '_blank'
    );

    document.getElementById('contactName').value    = '';
    document.getElementById('contactEmail').value   = '';
    document.getElementById('contactMessage').value = '';
  });
})();