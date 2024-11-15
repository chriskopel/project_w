import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:csv/csv.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: 'Team List',
      home: TeamListPage(),
    );
  }
}

class TeamListPage extends StatefulWidget {
  const TeamListPage({super.key});

  @override
  _TeamListPageState createState() => _TeamListPageState();
}

class _TeamListPageState extends State<TeamListPage> {
  List<String> userTeamNames = [];
  List<String> selectedTeams = [];
  List<String> filteredTeams = [];
  bool isLoading = true; // To control the loading indicator
  TextEditingController searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    loadCSV();
    searchController.addListener(updateFilteredTeams);
  }

  // Load the CSV data from the assets
  Future<void> loadCSV() async {
    final data = await rootBundle.loadString('assets/project_w_data.csv');
    List<List<dynamic>> csvTable = CsvToListConverter(eol: '\n', fieldDelimiter: ',').convert(data);

    // Extract team names
    List<String> teams = [];
    var headerRow = csvTable[0];
    var userTeamIndex = headerRow.indexOf('user_team');

    // Loop through rows and collect team names
    for (var row in csvTable.skip(1)) {
      var teamName = row[userTeamIndex]?.toString()?.trim();
      if (teamName != null && teamName.isNotEmpty) {
        teams.add(teamName);
      }
    }

    // Remove duplicates and sort
    var uniqueTeams = teams.toSet().toList();
    uniqueTeams.sort();

    // Update state with the list of teams
    setState(() {
      userTeamNames = uniqueTeams;
      filteredTeams = uniqueTeams;
      isLoading = false;
    });
  }

  // Filter teams based on search input
  void updateFilteredTeams() {
    String query = searchController.text.toLowerCase();
    setState(() {
      filteredTeams = userTeamNames
          .where((team) => team.toLowerCase().contains(query))
          .toList();
    });
  }

  // Toggle team selection
  void toggleSelection(String team) {
    setState(() {
      if (selectedTeams.contains(team)) {
        selectedTeams.remove(team);
      } else {
        selectedTeams.add(team);
      }
    });
  }

  // Navigate to the schedule page
  void navigateToSchedulePage(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SchedulePage(selectedTeams: selectedTeams),
      ),
    );
  }

  @override
  void dispose() {
    searchController.removeListener(updateFilteredTeams);
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Teams'),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator()) // Show loading indicator while data is loading
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: TextField(
                    controller: searchController,
                    decoration: const InputDecoration(
                      labelText: 'Search Teams',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: filteredTeams.length,
                    itemBuilder: (context, index) {
                      String team = filteredTeams[index];
                      return ListTile(
                        title: Text(team),
                        leading: Checkbox(
                          value: selectedTeams.contains(team),
                          onChanged: (_) {
                            toggleSelection(team);
                          },
                        ),
                      );
                    },
                  ),
                ),
                const Divider(),
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(
                    'Selected Teams: ${selectedTeams.join(', ')}',
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: ElevatedButton(
                    onPressed: selectedTeams.isEmpty
                        ? null // Disable button if no teams are selected
                        : () => navigateToSchedulePage(context),
                    child: const Text('Load Schedule'),
                  ),
                ),
              ],
            ),
    );
  }
}

class SchedulePage extends StatelessWidget {
  final List<String> selectedTeams;

  const SchedulePage({super.key, required this.selectedTeams});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Schedule'),
      ),
      body: ListView.builder(
        itemCount: selectedTeams.length,
        itemBuilder: (context, index) {
          return ListTile(
            title: Text(selectedTeams[index]),
          );
        },
      ),
    );
  }
}
