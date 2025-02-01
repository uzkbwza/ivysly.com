function updateRelativeTimes() {
  const elements = document.querySelectorAll('time[data-timeformat="relative"]');
  elements.forEach(function(element) {
    const dateString = element.getAttribute('datetime');
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    let relativeTimeText = '';
    if (diffInSeconds < 60) {
      relativeTimeText = 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      relativeTimeText = minutes + ' minute' + (minutes === 1 ? '' : 's');
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      relativeTimeText = hours + ' hour' + (hours === 1 ? '' : 's');
    } else if (diffInSeconds < 2592000) {
      const days = Math.floor(diffInSeconds / 86400);
      relativeTimeText = days + ' day' + (days === 1 ? '' : 's');
    } else if (diffInSeconds < 31536000) {
      const months = Math.floor(diffInSeconds / 2592000);
      relativeTimeText = months + ' month' + (months === 1 ? '' : 's');
    } else {
      const years = Math.floor(diffInSeconds / 31536000);
      relativeTimeText = years + ' year' + (years === 1 ? '' : 's');
    }

    element.textContent = relativeTimeText;
  });
}

// example: <time datetime="2022-10-15T09:30:00Z" data-timeformat="relative"></time>

// example: <time datetime="2023" data-timeformat="relative"></time>

// Update immediately, then run at a given interval
updateRelativeTimes();
setInterval(updateRelativeTimes, 60000);