const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Topics
  async getTopics() {
    return this.request('/topics');
  }

  async getTopic(topicId) {
    return this.request(`/topics/${topicId}`);
  }

  async createTopic(name) {
    return this.request('/topics', {
      method: 'POST',
      body: { name },
    });
  }

  async getSubtopics(topicId) {
    return this.request(`/topics/${topicId}/subtopics`);
  }

  async getTopicQuestions(topicId) {
    return this.request(`/topics/${topicId}/questions`);
  }

  async getTopicStats(topicId) {
    return this.request(`/topics/${topicId}/stats`);
  }

  // Quizzes
  async startQuiz(topicId, numQuestions = null) {
    let url = `/quizzes/start?topic_id=${topicId}`;
    if (numQuestions) {
      url += `&num_questions=${numQuestions}`;
    }
    return this.request(url, { method: 'GET' });
  }

  async gradeAnswer(questionId, userAnswer) {
    return this.request('/quizzes/grade', {
      method: 'POST',
      body: { question_id: questionId, user_answer: userAnswer },
    });
  }

  async getQuizResults(answers) {
    return this.request('/quizzes/results', {
      method: 'POST',
      body: answers,
    });
  }

  async getQuizHistory(topicId = null, limit = 20) {
    const params = new URLSearchParams();
    if (topicId) params.append('topic_id', topicId);
    params.append('limit', limit);
    return this.request(`/quizzes/history?${params.toString()}`);
  }

  async generateAdditionalQuestions(topicId) {
    return this.request(`/topics/${topicId}/questions/generate`, {
      method: 'POST',
    });
  }
}

export default new ApiService();

