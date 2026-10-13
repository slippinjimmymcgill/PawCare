export function formatPetAge(dobString: string | null): string {
  if (!dobString) {
    return "Age not specified";
  }

  const birthDate = new Date(dobString);
  if (isNaN(birthDate.getTime())) {
    return "Age not specified";
  }

  const today = new Date();
  let years = today.getFullYear() - birthDate.getFullYear();
  let months = today.getMonth() - birthDate.getMonth();
  const days = today.getDate() - birthDate.getDate();

  if (days < 0) {
    months -= 1;
  }
  if (months < 0) {
    years -= 1;
    months += 12;
  }

  if (years <= 0 && months <= 0) {
    const diffTime = Math.abs(today.getTime() - birthDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `${diffDays} day${diffDays === 1 ? "" : "s"} old`;
  }

  if (years <= 0) {
    return `${months} month${months === 1 ? "" : "s"} old`;
  }

  if (months === 0) {
    return `${years} year${years === 1 ? "" : "s"} old`;
  }

  return `${years} yr${years === 1 ? "" : "s"}, ${months} mo${months === 1 ? "" : "s"}`;
}

export function formatPetWeight(weightKg: number | null): string {
  if (weightKg === null || weightKg === undefined) {
    return "Not recorded";
  }
  return `${weightKg} kg`;
}
