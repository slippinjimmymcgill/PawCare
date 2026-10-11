from wireframe_lib import *

# ===================== 1. AUTH: Login + Register =====================
fig, ax, w, h = new_canvas(12.8, 7.2, "Auth — Login & Register (two states of one screen)")
# Login half
box(ax, 0.4, 0.4, 5.8, 6.2, fill="white")
ax.text(3.3, 0.9, "LOGIN", fontsize=11, fontweight="bold", ha="center", color=INK)
input_field(ax, 1.0, 1.6, 4.6, 0.6, "Email")
input_field(ax, 1.0, 2.4, 4.6, 0.6, "Password")
button(ax, 1.0, 3.3, 4.6, 0.6, "Log In")
ax.text(3.3, 4.15, "Forgot password?", fontsize=8.5, color=LINE, ha="center", style="italic")
ax.text(3.3, 4.7, "— or —", fontsize=8.5, color=LINE, ha="center")
ax.text(3.3, 5.2, "Don't have an account? Register", fontsize=8.5, color=LINE, ha="center", style="italic")

# Register half
box(ax, 6.6, 0.4, 5.8, 6.2, fill="white")
ax.text(9.5, 0.9, "REGISTER", fontsize=11, fontweight="bold", ha="center", color=INK)
input_field(ax, 7.2, 1.6, 4.6, 0.6, "Full name")
input_field(ax, 7.2, 2.4, 4.6, 0.6, "Email")
input_field(ax, 7.2, 3.2, 4.6, 0.6, "Password")
input_field(ax, 7.2, 4.0, 4.6, 0.6, "Confirm password")
button(ax, 7.2, 4.9, 4.6, 0.6, "Create Account")
ax.text(9.5, 5.75, "FR-01: passwords hashed; JWT session on success", fontsize=7.6, color=LINE, ha="center", style="italic")
save(fig, "01-auth")

# ===================== 2. PET PROFILE: list + create/edit =====================
fig, ax, w, h = new_canvas(12.8, 8.2, "Pet Profile — list (left) & create/edit form (right)")
navbar(ax, w, ["Dashboard","Pets","Assistant","Reminders"], active=1)
box(ax, 0.4, 1.0, 4.0, 6.8, fill="white")
ax.text(2.4, 1.4, "My Pets", fontsize=10.5, fontweight="bold", ha="center")
for i,n in enumerate(["[dog] Bruno","[cat] Mimi","+ Add pet"]):
    box(ax, 0.8, 1.9+i*1.1, 3.2, 0.85, label=n, fill=FILL2 if i<2 else "white", dashed=(i==2))

box(ax, 4.7, 1.0, 7.7, 6.8, fill="white")
ax.text(8.55, 1.4, "Edit Pet — Bruno", fontsize=10.5, fontweight="bold", ha="center")
fields = ["Name","Species (dog / cat)","Breed","Sex","Date of birth","Weight (kg)","Allergies (text)","Medical history (text)"]
y = 1.9
for f in fields:
    input_field(ax, 5.1, y, 6.9, 0.55, f)
    y += 0.7
button(ax, 5.1, y+0.1, 3.2, 0.55, "Save changes")
button(ax, 8.6, y+0.1, 3.4, 0.55, "Archive pet (soft-delete)", filled=False)
save(fig, "02-pet-profile")

# ===================== 3. HEALTH RECORDS: list + add-record =====================
fig, ax, w, h = new_canvas(12.8, 8.2, "Health Records — timeline (left) & add-record form (right)")
navbar(ax, w, ["Dashboard","Pets","Assistant","Reminders"], active=1)
box(ax, 0.4, 1.0, 6.9, 6.8, fill="white")
ax.text(3.85, 1.4, "Bruno — Records timeline", fontsize=10.5, fontweight="bold", ha="center")
rows = [("Vaccination","Rabies — given, next due in 11mo"),
        ("Weight log","24.5 kg"),
        ("Vet visit","Annual checkup — Dr. Khan"),
        ("Medication","Flea treatment — active"),
        ("Note","Limping slightly after walk")]
y=1.9
for t,d in rows:
    box(ax, 0.8, y, 6.1, 0.9, fill=FILL2)
    ax.text(1.0, y+0.3, t, fontsize=8.8, fontweight="bold", ha="left")
    ax.text(1.0, y+0.62, d, fontsize=8.0, ha="left", color=LINE)
    y += 1.05

box(ax, 7.6, 1.0, 4.8, 6.8, fill="white")
ax.text(10.0, 1.4, "Add record", fontsize=10.5, fontweight="bold", ha="center")
input_field(ax, 7.9, 1.9, 4.2, 0.55, "Type (visit / weight / note)")
input_field(ax, 7.9, 2.6, 4.2, 0.55, "Date")
input_field(ax, 7.9, 3.3, 4.2, 1.1, "Description")
input_field(ax, 7.9, 4.55, 4.2, 0.55, "Weight (kg) — if weight log")
box(ax, 7.9, 5.25, 4.2, 0.7, label="[+] Attach file", dashed=True)
button(ax, 7.9, 6.1, 4.2, 0.6, "Save record")
save(fig, "03-health-records")

# ===================== 4. SYMPTOM CHECKER =====================
fig, ax, w, h = new_canvas(12.8, 9.4, "Symptom Checker — submission (left) & results (right)", subtitle="\u26A0 safety-critical layout — urgency / confidence / sources / disclaimer are required elements, not polish", device="Desktop / Mobile")
navbar(ax, w, ["Dashboard","Pets","Assistant","Reminders"], active=2)
box(ax, 0.4, 1.0, 5.4, 7.8, fill="white")
ax.text(3.1, 1.4, "Describe the symptom — Bruno", fontsize=10.2, fontweight="bold", ha="center")
input_field(ax, 0.8, 2.0, 4.6, 2.0, "Free text: \"What's going on?\"")
ax.text(3.1, 4.25, "Optional structured details:", fontsize=8.6, color=LINE, ha="center")
input_field(ax, 0.8, 4.5, 4.6, 0.55, "Duration")
input_field(ax, 0.8, 5.2, 4.6, 0.55, "Severity (mild/mod/severe)")
input_field(ax, 0.8, 5.9, 4.6, 0.55, "Appetite / behavior change")
button(ax, 0.8, 6.7, 4.6, 0.65, "Get Assessment")
ax.text(3.1, 7.6, "FR-04: free text required; empty + no\nstructured input is rejected", fontsize=7.6, color=LINE, ha="center", style="italic")

box(ax, 6.2, 1.0, 6.2, 7.8, fill="white")
ax.text(9.3, 1.4, "Results", fontsize=10.2, fontweight="bold", ha="center")
box(ax, 6.6, 1.8, 5.4, 0.75, label="URGENCY: URGENT — see a vet within 24h", fill="#f0d9d9", safety=True,
    note=None, fs=9.3)
ax.text(9.3, 2.75, "(FR-05/FR-08 — Safety Layer can override this level;", fontsize=7.4, color="#C0392B", ha="center", style="italic")
ax.text(9.3, 2.95, "red-flag input forces Emergency regardless of model output)", fontsize=7.4, color="#C0392B", ha="center", style="italic")
box(ax, 6.6, 3.25, 5.4, 1.5, fill=FILL2)
ax.text(6.85, 3.55, "Possible concerns (ranked, with confidence):", fontsize=8.4, fontweight="bold", ha="left")
ax.text(6.85, 3.95, "1. Gastrointestinal upset — 62%", fontsize=8.2, ha="left")
ax.text(6.85, 4.25, "2. Dietary indiscretion — 41%", fontsize=8.2, ha="left")
ax.text(6.85, 4.55, "3. Insufficient info — consider a vet visit", fontsize=8.2, ha="left", color=LINE)
box(ax, 6.6, 5.0, 5.4, 1.1, fill=FILL2)
ax.text(6.85, 5.3, "Home-care guidance (if applicable):", fontsize=8.4, fontweight="bold", ha="left")
ax.text(6.85, 5.65, "Withhold food 12h, offer water...", fontsize=8.0, ha="left", color=LINE)
box(ax, 6.6, 6.25, 5.4, 0.65, label="\u26A0 When to see a vet: ...", fill="#f7ecec", safety=True, fs=8.6)
box(ax, 6.6, 7.0, 5.4, 0.55, label="Sources: [Merck Vet Manual \u00b7 2 more]", fill="white", dashed=True, fs=8.2)
box(ax, 6.6, 7.65, 5.4, 0.9, label="Not a diagnosis. This is decision support only —\nalways confirm with a veterinarian.", fill="#efefef", safety=True, fs=8.0)
save(fig, "04-symptom-checker")

# ===================== 5. ASSISTANT CHAT =====================
fig, ax, w, h = new_canvas(12.8, 8.6, "AI Assistant Chat — context-aware, source-cited", subtitle="\u26A0 safety-critical layout")
navbar(ax, w, ["Dashboard","Pets","Assistant","Reminders"], active=2)
box(ax, 0.4, 1.0, 12.0, 6.2, fill="white")
ax.text(0.7, 1.35, "Chatting about: Bruno (dog, 3y)", fontsize=8.6, color=LINE)
# user msg
box(ax, 7.6, 1.7, 4.4, 0.7, label="Is it OK to walk him after vaccination?", fill=FILL2, fs=8.6)
# assistant msg
box(ax, 0.8, 2.6, 7.6, 1.5, fill="white")
ax.text(1.0, 2.85, "Light activity is usually fine, but avoid strenuous", fontsize=8.4, ha="left")
ax.text(1.0, 3.12, "exercise for 24-48h. Watch for swelling at the injection", fontsize=8.4, ha="left")
ax.text(1.0, 3.39, "site or lethargy. [1][2]", fontsize=8.4, ha="left")
box(ax, 0.8, 4.2, 7.6, 0.5, label="[sources] [1] AAHA Vaccination Guidelines  [2] Merck Vet Manual", fill="white", dashed=True, fs=7.8, align="left", safety=True)
box(ax, 0.8, 4.85, 7.6, 0.45, label="This is general guidance, not a diagnosis for Bruno specifically.", fill="#efefef", fs=7.6, align="left", safety=True)
# red-flag example callout — own row, clear of the input bar
box(ax, 0.8, 5.5, 11.2, 0.55, fill="#f7ecec", dashed=True, safety=True,
    label="If a red-flag symptom is mentioned mid-chat, the Safety Layer overrides with an Emergency banner (FR-08)",
    fs=8.0)

input_field(ax, 0.8, 6.3, 9.6, 0.65, "Type a message…")
button(ax, 10.5, 6.3, 1.9, 0.65, "Send")
save(fig, "05-assistant-chat")

# ===================== 6. DASHBOARD =====================
fig, ax, w, h = new_canvas(12.8, 8.2, "Health Monitoring Dashboard — Bruno")
navbar(ax, w, ["Dashboard","Pets","Assistant","Reminders"], active=0)
box(ax, 0.4, 1.0, 6.0, 3.1, fill="white")
ax.text(3.4, 1.35, "Weight trend", fontsize=9.6, fontweight="bold", ha="center")
import numpy as np
xs = np.linspace(0.9, 5.9, 6); ys = [3.3,3.1,2.9,2.7,2.5,2.4]
ax.plot(xs, ys, color=INK, marker="o", lw=1.4)
ax.text(3.4, 3.9, "(empty state: \u201cNo weight logs yet — add one\u201d)", fontsize=7.4, color=LINE, ha="center", style="italic")

box(ax, 6.8, 1.0, 5.6, 3.1, fill="white")
ax.text(9.6, 1.35, "Upcoming reminders", fontsize=9.6, fontweight="bold", ha="center")
for i,r in enumerate(["Rabies booster — in 11mo","Deworming — in 3wk","Annual checkup — in 2mo"]):
    box(ax, 7.1, 1.7+i*0.65, 5.0, 0.5, label=r, fill=FILL2, fs=8.2, align="left")

box(ax, 0.4, 4.4, 6.0, 3.4, fill="white")
ax.text(3.4, 4.75, "Recent assessments", fontsize=9.6, fontweight="bold", ha="center")
for i,r in enumerate(["Oct 3 — Urgent (GI upset, 62%)","Sep 20 — Home-care (minor limp)"]):
    box(ax, 0.8, 5.1+i*0.7, 5.2, 0.55, label=r, fill=FILL2, fs=8.2, align="left")
ax.text(3.4, 6.7, "(empty state: \u201cNo assessments yet\u201d)", fontsize=7.4, color=LINE, ha="center", style="italic")

box(ax, 6.8, 4.4, 5.6, 3.4, fill="white")
ax.text(9.6, 4.75, "Record summary", fontsize=9.6, fontweight="bold", ha="center")
for i,r in enumerate(["3 vaccinations on file","1 active medication","6 health records total"]):
    box(ax, 7.1, 5.1+i*0.65, 5.0, 0.5, label=r, fill=FILL2, fs=8.2, align="left")
save(fig, "06-dashboard")

# ===================== 7. ADMIN =====================
fig, ax, w, h = new_canvas(12.8, 8.0, "Admin — user management (left) & knowledge-base documents (right)")
navbar(ax, w, ["Dashboard","Users","Knowledge Base","Flagged"], active=1)
box(ax, 0.4, 1.0, 6.0, 6.6, fill="white")
ax.text(3.4, 1.35, "Users", fontsize=10.2, fontweight="bold", ha="center")
for i,u in enumerate(["ayesha@...  owner  active","bilal@...  owner  active","admin@...  admin  active"]):
    box(ax, 0.8, 1.75+i*0.8, 5.2, 0.6, label=u, fill=FILL2, fs=8.3, align="left")

box(ax, 6.8, 1.0, 5.6, 6.6, fill="white")
ax.text(9.6, 1.35, "Knowledge-base documents", fontsize=10.2, fontweight="bold", ha="center")
for i,d in enumerate(["Merck Vet Manual — CC-BY","AAHA Guidelines — permitted use","WSAVA Nutrition Guide — pending license"]):
    box(ax, 7.1, 1.75+i*0.8, 5.0, 0.6, label=d, fill=FILL2, fs=8.0, align="left")
button(ax, 7.1, 4.3, 5.0, 0.55, "+ Upload document (triggers re-indexing)")
ax.text(9.6, 5.2, "FR-12: licensing field required before a document\nis ingestible (see schema-notes.md \u00a75)", fontsize=7.6, color=LINE, ha="center", style="italic")
save(fig, "07-admin")

print("all wireframes saved")
