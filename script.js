const hasMotionReduction = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (window.gsap && window.ScrollTrigger && !hasMotionReduction) {
  gsap.registerPlugin(ScrollTrigger);

  gsap.defaults({
    ease: "power3.out",
    duration: 1,
  });

  gsap.fromTo(
    ".site-header",
    { y: -20, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.9, ease: "power2.out" }
  );

  const heroTimeline = gsap.timeline({ defaults: { ease: "power3.out" } });
  heroTimeline
    .fromTo(
      ".hero-copy .reveal-item",
      { y: 42, opacity: 0 },
      { y: 0, opacity: 1, stagger: 0.12, duration: 1 },
      0
    )
    .fromTo(
      ".hero-stage",
      { scale: 0.94, opacity: 0, rotate: -2 },
      { scale: 1, opacity: 1, rotate: 0, duration: 1.2 },
      0.15
    )
    .fromTo(
      ".signal-card-main",
      { y: 36, opacity: 0 },
      { y: 0, opacity: 1, duration: 1 },
      0.35
    );

  gsap.to(".scan-beam", {
    yPercent: 120,
    opacity: 0.12,
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  gsap.to(".hero-stage", {
    y: 80,
    rotate: -1.5,
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  gsap.utils.toArray(".parallax-fast").forEach((item) => {
    gsap.to(item, {
      y: -80,
      x: 20,
      ease: "none",
      scrollTrigger: {
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
      },
    });
  });

  gsap.utils.toArray(".parallax-slow").forEach((item) => {
    gsap.to(item, {
      y: -40,
      x: -16,
      ease: "none",
      scrollTrigger: {
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
      },
    });
  });

  gsap.to(".flight-one", {
    scaleX: 1.15,
    opacity: 0.5,
    transformOrigin: "left center",
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  gsap.to(".flight-two", {
    scaleX: 0.88,
    opacity: 0.5,
    transformOrigin: "left center",
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  gsap.utils.toArray(".reveal-sequence").forEach((group) => {
    const items = group.querySelectorAll(".reveal-item");
    if (!items.length) return;

    gsap.fromTo(
      items,
      { y: 42, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        stagger: 0.14,
        duration: 0.95,
        scrollTrigger: {
          trigger: group,
          start: "top 78%",
          once: true,
        },
      }
    );
  });

  gsap.utils.toArray(".reveal-fade").forEach((item) => {
    gsap.fromTo(
      item,
      { y: 30, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.9,
        scrollTrigger: {
          trigger: item,
          start: "top 82%",
          once: true,
        },
      }
    );
  });

  gsap.fromTo(
    ".manifest-line",
    { y: 80, opacity: 0 },
    {
      y: 0,
      opacity: 1,
      stagger: 0.18,
      duration: 1,
      scrollTrigger: {
        trigger: ".pin-scene",
        start: "top center",
        once: true,
      },
    }
  );

  ScrollTrigger.matchMedia({
    "(min-width: 761px)": function () {
      gsap.timeline({
        scrollTrigger: {
          trigger: ".pin-scene",
          start: "top top",
          end: "+=1200",
          pin: ".pin-inner",
          scrub: true,
        },
      })
        .to(".manifest-line:nth-child(1)", { y: -10, opacity: 0.35 }, 0)
        .to(".manifest-line:nth-child(2)", { y: -30, opacity: 0.65 }, 0.18)
        .to(".manifest-line:nth-child(3)", { y: -54, opacity: 1 }, 0.35);
    },
  });

  ScrollTrigger.refresh();
} else {
  document
    .querySelectorAll(".reveal-item, .reveal-fade, .manifest-line")
    .forEach((item) => {
      item.style.opacity = "1";
      item.style.transform = "none";
    });
}
