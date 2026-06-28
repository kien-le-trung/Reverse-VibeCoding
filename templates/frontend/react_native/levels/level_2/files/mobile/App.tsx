import { useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";

type Screen = "home" | "todos";

export default function App() {
  const [screen, setScreen] = useState<Screen>("home");

  return (
    <SafeAreaView style={styles.shell}>
      <View style={styles.header}>
        <Text style={styles.title}>Reverse Vibe Coding</Text>
      </View>

      <View style={styles.nav}>
        <Pressable accessibilityRole="button" onPress={() => setScreen("home")} style={styles.navButton}>
          <Text>Home</Text>
        </Pressable>
        <Pressable accessibilityRole="button" onPress={() => setScreen("todos")} style={styles.navButton}>
          <Text>Todos</Text>
        </Pressable>
      </View>

      <View style={styles.content}>
        {screen === "home" ? <Text>Choose a project screen.</Text> : <Text>Todo screen placeholder.</Text>}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  shell: {
    backgroundColor: "#f7f7f2",
    flex: 1,
  },
  header: {
    borderBottomColor: "#d8d8d0",
    borderBottomWidth: 1,
    padding: 20,
  },
  title: {
    color: "#202124",
    fontSize: 22,
    fontWeight: "700",
  },
  nav: {
    flexDirection: "row",
    gap: 8,
    padding: 16,
  },
  navButton: {
    backgroundColor: "#ffffff",
    borderColor: "#d8d8d0",
    borderRadius: 6,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  content: {
    padding: 20,
  },
});

