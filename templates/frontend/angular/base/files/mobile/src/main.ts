import { bootstrapApplication } from "@angular/platform-browser";
import { Component } from "@angular/core";

@Component({ selector: "app-root", standalone: true, template: `<main><h1>Reverse Vibe Coding</h1><p>Angular frontend template.</p></main>` })
class AppComponent {}

bootstrapApplication(AppComponent);
