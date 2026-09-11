(() => {
  const registerPassword = document.getElementById("register-password");
  const meterFill = document.getElementById("password-meter-fill");
  const meterText = document.getElementById("password-strength-text");
  if (registerPassword && meterFill && meterText) {
    const updateStrength = () => {
      const value = registerPassword.value;
      let score = 0;
      if (value.length >= 9) score += 1;
      if (/[A-Z]/.test(value)) score += 1;
      if (/[0-9]/.test(value)) score += 1;
      if (/[^A-Za-z0-9]/.test(value)) score += 1;

      const pct = (score / 4) * 100;
      meterFill.style.width = `${pct}%`;
      meterFill.classList.remove("s-weak", "s-medium", "s-strong");
      if (score <= 1) {
        meterFill.classList.add("s-weak");
        meterText.textContent = "Weak";
      } else if (score <= 3) {
        meterFill.classList.add("s-medium");
        meterText.textContent = "Medium";
      } else {
        meterFill.classList.add("s-strong");
        meterText.textContent = "Strong";
      }
    };

    registerPassword.addEventListener("input", updateStrength);
    updateStrength();
  }

  const toggles = document.querySelectorAll("[data-toggle-password]");
  toggles.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-toggle-password");
      const input = targetId ? document.getElementById(targetId) : null;
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      btn.classList.toggle("is-open", show);
    });
  });

  const track = document.querySelector(".video-track");
  if (track) {
    const slides = track.querySelectorAll(".slide");
    if (slides.length > 1) {
      let index = 0;
      setInterval(() => {
        index = (index + 1) % slides.length;
        track.style.transform = `translateX(-${index * 100}%)`;
      }, 4200);
    }
  }

  const targets = document.querySelectorAll(".reveal-up, .reveal-right");
  if (!targets.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  targets.forEach((el) => observer.observe(el));
})();
