/* Unity AI Harness — Website interactions */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize Animate On Scroll
  AOS.init({
    once: true,
    offset: 80,
    duration: 700,
    easing: 'ease-out-cubic'
  });

  // Initialize Mermaid with dark, animated-friendly config
  mermaid.initialize({
    startOnLoad: true,
    theme: 'dark',
    securityLevel: 'loose',
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: 'basis'
    },
    themeVariables: {
      fontFamily: 'Inter, sans-serif',
      primaryColor: '#0f172a',
      primaryTextColor: '#e2e8f0',
      primaryBorderColor: '#22d3ee',
      lineColor: '#818cf8',
      secondaryColor: '#1e293b',
      tertiaryColor: '#312e81'
    }
  });

  // Highlight active nav link on scroll
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('nav a[href^="#"]');

  if (sections.length && navLinks.length) {
    const observer = new IntersectionObserver(
      function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            navLinks.forEach(function(link) {
              link.classList.remove('text-cyan-400');
              if (link.getAttribute('href') === '#' + entry.target.id) {
                link.classList.add('text-cyan-400');
              }
            });
          }
        });
      },
      { rootMargin: '-40% 0px -55% 0px' }
    );

    sections.forEach(function(section) {
      observer.observe(section);
    });
  }
});
