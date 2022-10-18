// User cannot access page unless they have sufficient permission
const protectedRoutes = [];
const protectedOrganizationRoutes = [];
if (localStorage.getItem("token") === null) {
  window.location.href = "/login";
}
