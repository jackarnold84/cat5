export const timeSince = (timestamp) => {
  const now = Math.floor(Date.now() / 1000);
  const diff = now - timestamp;

  const seconds = diff;
  const minutes = Math.floor(diff / 60);
  const hours = Math.floor(diff / 3600);
  const days = Math.floor(diff / 86400);
  const years = Math.floor(diff / 31536000);

  if (years > 0) {
    return years === 1 ? `${years} year` : `${years} years`;
  } else if (days > 0) {
    return days === 1 ? `${days} day` : `${days} days`;
  } else if (hours > 0) {
    return hours === 1 ? `${hours} hour` : `${hours} hours`;
  } else if (minutes > 0) {
    return minutes === 1 ? `${minutes} minute` : `${minutes} minutes`;
  } else {
    return seconds === 1 ? `${seconds} second` : `${seconds} seconds`;
  }
};