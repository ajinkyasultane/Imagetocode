import 'package:flutter/material.dart';

void main() {
  runApp(const GeneratedApp());
}

class GeneratedApp extends StatelessWidget {
  const GeneratedApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "signup",
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)),
        useMaterial3: true,
      ),
      home: const GeneratedHome(),
    );
  }
}

class GeneratedHome extends StatelessWidget {
  const GeneratedHome({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("signup")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
              const SizedBox(height: 8),
              Text("signup", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Text("Email"),
              const SizedBox(height: 12),
              TextField(
                obscureText: false,
                decoration: InputDecoration(
                  hintText: "email",
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              Text("Password"),
              const SizedBox(height: 12),
              TextField(
                obscureText: true,
                decoration: InputDecoration(
                  hintText: "password",
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {},
                  child: Text("Continue"),
                ),
              ),
              const SizedBox(height: 12),
              Container(
                height: 140,
                decoration: BoxDecoration(
                  color: Color(0xFFF2F2F2),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Color(0xFFE5E7EB)),
                ),
                alignment: Alignment.center,
                child: const Text("image"),
              ),
              const SizedBox(height: 8),
              Text("© Piyush 2025"),
          ],
        ),
      ),
    );
  }
}