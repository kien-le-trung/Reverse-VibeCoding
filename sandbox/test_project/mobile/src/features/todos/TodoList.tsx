import { FlatList, StyleSheet, Text, View } from "react-native";

import type { Todo } from "./types";

type Props = {
  todos: Todo[];
};

export function TodoList({ todos }: Props) {
  return (
    <FlatList
      data={todos}
      keyExtractor={(item) => String(item.id)}
      renderItem={({ item }) => (
        <View style={styles.row}>
          <Text style={styles.title}>{item.title}</Text>
          <Text>{item.completed ? "Done" : "Open"}</Text>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  row: {
    borderBottomColor: "#d8d8d0",
    borderBottomWidth: 1,
    paddingVertical: 12,
  },
  title: {
    color: "#202124",
    fontSize: 16,
    fontWeight: "600",
  },
});

