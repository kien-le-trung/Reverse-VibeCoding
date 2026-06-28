import { bootstrapApplication } from "@angular/platform-browser";
import { Component } from "@angular/core";

@Component({ selector: "app-root", standalone: true, template: `<main><h1>Reverse Vibe Coding</h1><nav><button (click)="screen='home'">Home</button><button (click)="screen='todos'">Todos</button></nav><p *ngIf="screen === 'home'">Choose a project screen.</p><p *ngIf="screen === 'todos'">Todo screen placeholder.</p></main>` })
class AppComponent { screen: "home" | "todos" = "home"; }

bootstrapApplication(AppComponent);
