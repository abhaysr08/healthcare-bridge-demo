export function getHomeRouteForRole(role) {
  switch (role) {
    case 'admin':
      return '/admin';
    case 'doctor':
      return '/doctor';
    case 'nurse':
      return '/nurse';
    default:
      return '/chat';
  }
}
