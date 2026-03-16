document.addEventListener("DOMContentLoaded", function () {
  const userType = document.getElementById("id_user_type");
  const studentFieldIds = [
    "id_student_id",
    "id_faculty",
    "id_study_level",
    "id_graduation_year",
  ];

  if (!userType) return;

  function toggleStudentFields() {
    const isStudent = userType.value === "student";

    studentFieldIds.forEach((id) => {
      const field = document.getElementById(id);
      if (!field) return;
      const wrapper = field.closest(".mb-3");
      if (!wrapper) return;
      wrapper.style.display = isStudent ? "" : "none";
    });
  }

  toggleStudentFields();
  userType.addEventListener("change", toggleStudentFields);
});
