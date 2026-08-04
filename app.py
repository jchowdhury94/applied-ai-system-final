from datetime import date

import streamlit as st
import streamlit.components.v1 as components

import ai_assistant
from pawpal_system import Owner, Pet, Task, Scheduler


def clear_everything():
    keys_to_clear = [
        "owner",
        "last_ai_result",
        "owner_name_input",
        "pet_name_input",
        "species_input",
        "pet_age_input",
        "pet_needs_input",
        "task_pet_input",
        "task_description_input",
        "task_time_input",
        "task_frequency_input",
        "ai_question",
        "confirm_clear",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


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

st.divider()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        available_time=120, preferred_times=["morning"], task_priorities=[]
    )
owner = st.session_state.owner

st.subheader("Add a Pet")
owner_name = st.text_input(
    "Owner name",
    placeholder="Enter owner name",
    key="owner_name_input"
)

pet_name = st.text_input(
    "Pet name",
    placeholder="Enter pet name",
    key="pet_name_input"
)

species = st.selectbox(
    "Species",
    ["Select a species", "dog", "cat", "other"],
    key="species_input"
)

age = st.number_input(
    "Pet age",
    min_value=0,
    max_value=50,
    value=None,
    placeholder="Enter pet age",
    key="pet_age_input"
)

needs = st.text_input(
    "Pet needs (comma-separated)",
    placeholder="For example: walk, feed",
    key="pet_needs_input"
)

if st.button("Add pet"):
    if not owner_name.strip():
        st.warning("Please enter the owner's name.")
    elif not pet_name.strip():
        st.warning("Please enter the pet's name.")
    elif species == "Select a species":
        st.warning("Please select a species.")
    elif age is None:
        st.warning("Please enter the pet's age.")
    else:
        pet = Pet(
            name=pet_name.strip(),
            species=species,
            age=int(age),
            needs=[
                need.strip()
                for need in needs.split(",")
                if need.strip()
            ],
        )
        owner.add_pet(pet)
        st.success(f"Added {pet.name} to {owner_name}'s pets.")

st.markdown("### Tasks")

if not owner.pets:
    st.info("Add a pet above before creating tasks.")
else:
    pet_names = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Pet", pet_names, key="task_pet_input")
    selected_pet = owner.get_pet(selected_pet_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        description = st.text_input(
            "Task description",
            placeholder="For example: Morning walk",
            key="task_description_input"
        )
    with col2:
        time = st.text_input(
            "Time",
            placeholder="For example: 07:00",
            key="task_time_input"
        )
    with col3:
        frequency = st.selectbox(
            "Frequency",
            ["daily", "weekly", "monthly"],
            key="task_frequency_input"
        )

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
with st.expander("Example questions"):
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

st.divider()
st.subheader("Reset Application")

confirm_clear = st.checkbox(
    "I understand that this will remove all pets and tasks from this session.",
    key="confirm_clear",
)

if st.button(
    "Clear Everything",
    type="primary",
    disabled=not confirm_clear,
):
    clear_everything()
    # Streamlit's text_input/number_input widgets don't visually reset after
    # st.rerun() once a user has typed into them - only a full page reload
    # re-syncs their displayed value with the cleared session state.
    components.html("<script>window.parent.location.reload()</script>", height=0)
