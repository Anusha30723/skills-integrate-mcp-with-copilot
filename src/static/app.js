document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authForm = document.getElementById("auth-form");
  const registerButton = document.getElementById("register-btn");
  const logoutButton = document.getElementById("logout-btn");
  const authStatus = document.getElementById("auth-status");
  let accessToken = sessionStorage.getItem("accessToken");
  let currentUser = sessionStorage.getItem("currentUser");

  function authHeaders() {
    return accessToken
      ? { Authorization: `Bearer ${accessToken}` }
      : {};
  }

  function showAuthStatus(message, isError = false) {
    authStatus.textContent = message;
    authStatus.className = isError ? "error" : "success";
  }

  function updateAuthControls() {
    const isLoggedIn = Boolean(accessToken && currentUser);
    authForm.classList.toggle("hidden", isLoggedIn);
    logoutButton.classList.toggle("hidden", !isLoggedIn);
    if (isLoggedIn) {
      showAuthStatus(`Logged in as ${currentUser}`);
    } else {
      authStatus.className = "hidden";
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span>${
                        email === currentUser
                          ? `<button class="delete-btn" data-activity="${name}" title="Unregister yourself">Remove</button>`
                          : ""
                      }</li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
          headers: authHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  authForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("auth-email").value;
    const password = document.getElementById("auth-password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json();
      if (!response.ok) {
        showAuthStatus(result.detail || "Unable to log in", true);
        return;
      }

      accessToken = result.access_token;
      currentUser = result.email;
      sessionStorage.setItem("accessToken", accessToken);
      sessionStorage.setItem("currentUser", currentUser);
      authForm.reset();
      updateAuthControls();
      fetchActivities();
    } catch (error) {
      showAuthStatus("Unable to log in. Please try again.", true);
      console.error("Error logging in:", error);
    }
  });

  registerButton.addEventListener("click", async () => {
    const email = document.getElementById("auth-email").value;
    const password = document.getElementById("auth-password").value;
    if (!email || password.length < 8) {
      showAuthStatus("Enter an email and a password of at least 8 characters", true);
      return;
    }

    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json();
      showAuthStatus(
        response.ok ? "Account created. You can now log in." : result.detail || "Unable to create account",
        !response.ok
      );
    } catch (error) {
      showAuthStatus("Unable to create account. Please try again.", true);
      console.error("Error creating account:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    await fetch("/auth/logout", { method: "POST", headers: authHeaders() });
    accessToken = null;
    currentUser = null;
    sessionStorage.removeItem("accessToken");
    sessionStorage.removeItem("currentUser");
    updateAuthControls();
    fetchActivities();
  });

  // Initialize app
  updateAuthControls();
  fetchActivities();
});
