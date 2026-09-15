/** React Native Mobile App Entry Point — Eco Nojin. */

import React from 'react';
import {
  SafeAreaProvider,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  NavigationContainer,
} from 'react-native';

// Navigation
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

// Screens
import DashboardScreen from './screens/DashboardScreen';
import AdvisoryScreen from './screens/AdvisoryScreen';
import MarketplaceScreen from './screens/MarketplaceScreen';
import AdvisoryChatScreen from './screens/AdvisoryChatScreen';
import ProfileScreen from './screens/ProfileScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, string> = {
            Dashboard: focused ? 'home' : 'home-outline',
            Advisory: focused ? 'chatbubble' : 'chatbubble-outline',
            Marketplace: focused ? 'storefront' : 'storefront-outline',
            Profile: focused ? 'person' : 'person-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'home'} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#0071e3',
        tabBarInactiveTintColor: 'gray',
        tabBarLabelStyle: { fontSize: 10, fontWeight: '600' },
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Advisory" component={AdvisoryScreen} />
      <Tab.Screen name="Marketplace" component={MarketplaceScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
        <SafeAreaView style={styles.container}>
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Group>
              <Stack.Screen name="Main" component={MainTabNavigator} />
              <Stack.Screen name="AdvisoryChat" component={AdvisoryChatScreen} />
            </Stack.Group>
          </Stack.Navigator>
        </SafeAreaView>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f7',
  },
});
