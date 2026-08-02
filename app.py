from datetime import date

import streamlit as st

import ai_assistant
from pawpal_system import Owner, Pet, Task, Scheduler


def _render_ai_result(result):
    """Render one ai_assistant.answer_question() result dict in the UI.

    Only reads from `result` - never touches session state or PawPal+ objects,
    so it cannot be used to add, delete, complete, or reschedule anything.
    """
    st.markdown(f"**Answer:** {result.get('answer') or '(no answer available)'}")

    st.caption(f"Detected intent: {result.get('intent') or 'none'}")
    if result.get("detected_pet"):
        st.caption(f"Detected pet: {result['detected_pet']}")

    if result.get("fallback_used"):
        st.info(
            "PawPal+ used a deterministic answer based directly on retrieved "
            "records instead of an AI-generated answer "
            f"(reason: {result.get('fallback_reason') or 'unknown'})."
        )

    validation_result = result.get("validation_result")
    if validation_result:
        st.caption(f"Validation confidence: {validation_result.get('confidence')}")

    retrieval_result = result.get("retrieval_result")
    with st.expander("Retrieved PawPal+ Context"):
        st.caption("This is the information PawPal+ AI used to ground its answer.")
        if retrieval_result:
            st.text(retrieval_result.get("context_text") or "No context available.")
            st.caption(f"Records retrieved: {len(retrieval_result.get('records') or [])}")
            st.caption(f"Detected intent: {retrieval_result.get('intent') or 'none'}")
            if retrieval_result.get("detected_pet"):
                st.caption(f"Detected pet: {retrieval_result['detected_pet']}")
        else:
            st.caption("No context was retrieved for this question.")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        available_time=120, preferred_times=["morning"], task_priorities=[]
    )
owner = st.session_state.owner

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Pet age", min_value=0, max_value=50, value=2)
needs = st.text_input("Pet needs (comma-separated)", value="walk, feed")

if st.button("Add pet"):
    pet = Pet(
        name=pet_name,
        species=species,
        age=int(age),
        needs=[need.strip() for need in needs.split(",") if need.strip()],
    )
    owner.add_pet(pet)
    st.success(f"Added {pet.name} to {owner_name}'s pets.")

st.markdown("### Tasks")
st.caption("Add a few tasks. Tasks are attached to the selected pet.")

if not owner.pets:
    st.info("Add a pet above before creating tasks.")
else:
    pet_names = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Pet", pet_names)
    selected_pet = owner.get_pet(selected_pet_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        description = st.text_input("Task description", value="Morning walk")
    with col2:
        time = st.text_input("Time", value="07:00")
    with col3:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])

    if st.button("Add task"):
        task = Task(description=description, time=time, frequency=frequency)
        selected_pet.add_task(task)
        st.success(f"Added task to {selected_pet.name}.")

st.divider()

st.subheader("Current Pets & Tasks")

if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner.pets:
        st.markdown(f"**{pet.get_summary()}**")
        tasks = pet.get_tasks()
        if tasks:
            for task in tasks:
                st.write(f"- {task.get_summary()}")
        else:
            st.caption("No tasks yet.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if not owner.pets:
        st.info("Add a pet and some tasks before generating a schedule.")
    else:
        scheduler = Scheduler(owner)
        scheduler.generate_plan()

        st.table(
            [
                {
                    "Time": task.time,
                    "Task": task.description,
                    "Pet": task.pet.name if task.pet else "",
                    "Frequency": task.frequency,
                    "Completed": "Yes" if task.completed else "No",
                }
                for task in scheduler.selected_tasks
            ]
        )

        for tasks in scheduler.conflicts:
            details = ", ".join(
                f"{t.description} ({t.pet.name})" if t.pet else t.description
                for t in tasks
            )
            st.warning(f"Conflict at {tasks[0].time}: {details}.")

st.divider()

st.subheader("Ask PawPal+ AI")
st.markdown(
    "This assistant answers questions using the pets and tasks currently "
    "stored in this Streamlit session (`st.session_state.owner`). It is "
    "**read-only** - it cannot add, delete, complete, or reschedule anything."
)
st.caption(
    "PawPal+ AI does not provide veterinary diagnosis or treatment advice."
)
with st.expander("Example questions you can ask"):
    st.markdown(
        """
- What tasks are incomplete?
- What tasks are completed?
- What tasks does Mochi have?
- What is today's schedule?
- Are there any scheduling conflicts?
- What task should I do next?
"""
    )

ai_question = st.text_input("Ask a question about your pets and tasks", key="ai_question")

if st.button("Ask PawPal+ AI"):
    if not ai_question or not ai_question.strip():
        st.warning("Please enter a question before submitting.")
    else:
        st.session_state.last_ai_result = ai_assistant.answer_question(
            ai_question, owner, reference_date=date.today()
        )

if "last_ai_result" in st.session_state:
    _render_ai_result(st.session_state.last_ai_result)
