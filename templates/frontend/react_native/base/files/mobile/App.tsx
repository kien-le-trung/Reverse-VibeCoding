import { StatusBar } from "expo-status-bar";
import { StyleSheet, Text, View } from "react-native";

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Reverse Vibe Coding</Text>
      <Text style={styles.body}>Mobile starter is running.</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    backgroundColor: "#f7f7f2",
    flex: 1,
    justifyContent: "center",
    padding: 24,
  },
  title: {
    color: "#202124",
    fontSize: 24,
    fontWeight: "700",
    marginBottom: 8,
  },
  body: {
    color: "#4b5563",
    fontSize: 16,
    textAlign: "center",
  },
});

